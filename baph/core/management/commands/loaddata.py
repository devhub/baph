from __future__ import unicode_literals
import glob
import gzip
from itertools import product
import logging
import os
import zipfile
from optparse import make_option
import warnings
try:
    import bz2
    has_bz2 = True
except ImportError:
    has_bz2 = False

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.core import serializers
from django.utils.datastructures import SortedDict
from django.utils.functional import cached_property, memoize
from django.utils._os import upath
from sqlalchemy.orm.util import identity_key
from sqlalchemy.orm.attributes import instance_dict

from baph.core.management.base import BaseCommand
from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import get_app_paths
from baph.db.orm import ORM


logger = logging.getLogger(__name__)
orm = ORM.get()

def humanize(dirname):
    return "'%s'" % dirname if dirname else 'absolute path'

class SingleZipReader(zipfile.ZipFile):

    def __init__(self, *args, **kwargs):
        zipfile.ZipFile.__init__(self, *args, **kwargs)
        if len(self.namelist()) != 1:
            raise ValueError("Zip-compressed fixtures must contain one file.")

    def read(self):
        return zipfile.ZipFile.read(self, self.namelist()[0])

class Command(BaseCommand):
    help = 'Installs the named fixture(s) in the database.'
    args = "fixture [fixture ...]"
    
    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, 
            help='Nominates a specific database to load fixtures into. '
                 'Defaults to the "default" database.'),
        make_option('--ignorenonexistent', '-i', action='store_true',
            dest='ignore', default=False, help='Ignores entries in the '
                'serialized data for fields that do not currently exist '
                'on the model.'),
    )

    def handle(self, *fixture_labels, **options):
    
        self.ignore = options.get('ignore')
        self.using = options.get('database')

        if not len(fixture_labels):
            raise CommandError(
                    "No database fixture specified. Please provide the path "
                    "of at least one fixture in the command line.")

        # verbosity is ignored now, in favor of controlling console output
        # via settings.LOGGING (in order to apply different levels to
        # different types of logging)
        self.verbosity = int(options.get('verbosity'))
        self.loaddata(fixture_labels)

    def loaddata(self, fixture_labels):
        connection = orm = ORM.get(self.using)

        # Keep a count of the installed objects and fixtures
        self.fixture_count = 0
        self.loaded_object_count = 0
        self.fixture_object_count = 0
        self.models = set()

        self.serialization_formats = serializers.get_public_serializer_formats()
        self.compression_formats = {
            None:   open,
            'gz':   gzip.GzipFile,
            'zip':  SingleZipReader
        }
        if has_bz2:
            self.compression_formats['bz2'] = bz2.BZ2File

        for fixture_label in fixture_labels:
            self.load_label(fixture_label)

        # Since we disabled constraint checks, we must manually check for
        # any invalid keys that might have been added
        # TODO: implement this
        '''
        table_names = [model._meta.db_table for model in self.models]
        try:
            connection.check_constraints(table_names=table_names)
        except Exception as e:
            e.args = ("Problem installing fixtures: %s" % e,)
            raise
        '''
        # If we found even one object in a fixture, we need to reset the
        # database sequences.
        # TODO: implement this
        '''
        if self.loaded_object_count > 0:
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), self.models)
            if sequence_sql:
                if self.verbosity >= 2:
                    self.stdout.write("Resetting sequences\n")
                cursor = connection.cursor()
                for line in sequence_sql:
                    cursor.execute(line)
                cursor.close()
        '''
        if self.fixture_object_count == self.loaded_object_count:
            logger.info("Installed %d object(s) from %d fixture(s)" %
                    (self.loaded_object_count, self.fixture_count))
        else:
            logger.info("Installed %d object(s) (of %d) from %d fixture(s)" %
                    (self.loaded_object_count, self.fixture_object_count,
                     self.fixture_count))

    def load_label(self, fixture_label):
        """
        Loads fixtures files for a given label.
        """
        session = orm.sessionmaker()
        session.expunge_all()
        
        logger.info('Loading fixture label: "%s"' % fixture_label)
        identity_map = SortedDict()
        for fixture_file, fixture_dir, fixture_name \
                    in self.find_fixtures(fixture_label):
            logger.info('  Loading fixture: %s' % fixture_file)
            _, ser_fmt, cmp_fmt = self.parse_name(
                    os.path.basename(fixture_file))
            open_method = self.compression_formats[cmp_fmt]
            fixture = open_method(fixture_file, 'r')
            try:
                self.fixture_count += 1
                objects_in_fixture = 0
                loaded_objects_in_fixture = 0
                    
                objects = serializers.deserialize(ser_fmt, fixture,
                    using=self.using, ignorenonexistent=self.ignore)

                for obj in objects:
                    objects_in_fixture += 1
                    # TODO: implement routing
                    if True: #router.allow_syncdb(self.using, obj.object.__class__):
                        loaded_objects_in_fixture += 1
                        self.models.add(type(obj))
                        cls, key = identity_key(instance=obj)
                        if any(part is None for part in key):
                            # we can't generate an explicit key with this info
                            session.add(obj)
                            continue
                        if (cls, key) in identity_map:
                            # remove the existing fixture object
                            session.expunge(identity_map[(cls, key)])
                        identity_map[(cls, key)] = obj
                        session.add(obj)
                        
                self.loaded_object_count += loaded_objects_in_fixture
                self.fixture_object_count += objects_in_fixture
            except AttributeError:
                # if attributes don't match up, it could be a base fixture 
                # being applied to a subclassed object. We can ignore this
                # fixture
                logger.info('    Fixture could not be loaded due to attribute'
                            ' errors. Skipping')
                continue
            except Exception as e:
                if not isinstance(e, CommandError):
                    e.args = ("Problem installing fixture '%s': %s" 
                              % (fixture_file, e),)
                raise
            finally:
                fixture.close()

            # If the fixture we loaded contains 0 objects, assume that an
            # error was encountered during fixture loading.
            if objects_in_fixture == 0:
                raise CommandError(
                        "No fixture data found for '%s'. "
                        "(File format may be invalid.)" % fixture_name)

        session.execute('SET foreign_key_checks=0')
        session.commit()
        session.execute('SET foreign_key_checks=1')


    def _find_fixtures(self, fixture_label):
        """
        Finds fixture files for a given label.
        """
        fixture_name, ser_fmt, cmp_fmt = self.parse_name(fixture_label)
        #databases = [self.using, None]
        cmp_fmts = list(self.compression_formats.keys()) \
                if cmp_fmt is None else [cmp_fmt]
        ser_fmts = serializers.get_public_serializer_formats() \
                if ser_fmt is None else [ser_fmt]

        # Check kept for backwards-compatibility; it doesn't look very useful.
        if '.' in os.path.basename(fixture_name):
            raise CommandError(
                    "Problem installing fixture '%s': %s is not a known "
                    "serialization format." % tuple(fixture_name.rsplit('.')))

        if os.path.isabs(fixture_name):
            fixture_dirs = [os.path.dirname(fixture_name)]
            fixture_name = os.path.basename(fixture_name)
        else:
            fixture_dirs = self.fixture_dirs

        suffixes = ('.'.join(ext for ext in combo if ext)
                for combo in product(ser_fmts, cmp_fmts))
        targets = set('.'.join((fixture_name, suffix)) for suffix in suffixes)

        fixture_files = []
        for fixture_dir in fixture_dirs:
            logger.debug("  Checking %s for fixtures..." 
                        % humanize(fixture_dir))
            fixture_files_in_dir = []
            for candidate in glob.iglob(os.path.join(fixture_dir, 
                                                     fixture_name + '*')):
                if os.path.basename(candidate) in targets:
                    # Save the fixture_dir and fixture_name for future 
                    # error messages.
                    logger.debug("    Found fixture: %s" % candidate)
                    fixture_files_in_dir.append((candidate, fixture_dir,
                                                fixture_name))

            if not fixture_files_in_dir:
                logger.debug("    No fixture found")

            # Check kept for backwards-compatibility; it isn't clear why
            # duplicates are only allowed in different directories.
            if len(fixture_files_in_dir) > 1:
                raise CommandError(
                        "Multiple fixtures named '%s' in %s. Aborting." %
                        (fixture_name, humanize(fixture_dir)))
            fixture_files.extend(fixture_files_in_dir)

        if fixture_name != 'initial_data' and not fixture_files:
            # Warning kept for backwards-compatibility; why not an exception?
            warnings.warn("No fixture named '%s' found." % fixture_name)

        return fixture_files

    _label_to_fixtures_cache = {}
    find_fixtures = memoize(_find_fixtures, _label_to_fixtures_cache, 2)

    @cached_property
    def fixture_dirs(self):
        """
        Return a list of fixture directories.

        The list contains the 'fixtures' subdirectory of each installed
        application, if it exists, the directories in FIXTURE_DIRS, and the
        current directory.
        """
        dirs = []
        for path in get_app_paths():
            d = os.path.join(os.path.dirname(path), 'fixtures')
            if os.path.isdir(d):
                dirs.append(d)
        dirs.extend(list(settings.FIXTURE_DIRS))
        dirs.append('')
        dirs = [upath(os.path.abspath(os.path.realpath(d))) for d in dirs]
        return dirs

    def parse_name(self, fixture_name):
        """
        Splits fixture name in name, serialization format, compression format.
        """
        parts = fixture_name.rsplit('.', 2)

        if len(parts) > 1 and parts[-1] in self.compression_formats:
            cmp_fmt = parts[-1]
            parts = parts[:-1]
        else:
            cmp_fmt = None

        if len(parts) > 1 and parts[-1] in self.serialization_formats:
            ser_fmt = parts[-1]
            parts = parts[:-1]
        else:
            ser_fmt = None

        name = '.'.join(parts)

        return name, ser_fmt, cmp_fmt

