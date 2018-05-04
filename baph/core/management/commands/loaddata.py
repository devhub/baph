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
from django.db import (
    DEFAULT_DB_ALIAS, DatabaseError, IntegrityError, connections, router,
    transaction,
)
from django.utils._os import upath
from django.utils.datastructures import SortedDict
from django.utils.functional import cached_property, memoize
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.session import Session

from baph.core.management.new_base import BaseCommand
from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import get_app_paths
from baph.db.models.utils import identity_key
from baph.db.orm import ORM
from baph.utils.glob import glob_escape


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

def get_deferred_updates(session):
    deferred = []
    for obj in session:
        attrs = obj.post_update_attrs
        if not attrs:
            continue
        filters = obj.pk_as_query_filters()
        if filters is None:
            continue
        update = {}
        for attr in attrs:
            if getattr(obj, attr.key):
                update[attr] = getattr(obj, attr.key)
                delattr(obj, attr.key)
        if update:
            deferred.append((type(obj), filters, update))
    return deferred

class Command(BaseCommand):
    help = 'Installs the named fixture(s) in the database.'
    missing_args_message = ("No database fixture specified. Please provide "
                            "the path of at least one fixture in the command "
                            "line.")
    
    def add_arguments(self, parser):
      parser.add_argument(
        'args', metavar='fixture', nargs='+', help='Fixture labels.')
      parser.add_argument(
        '--database', action='store', dest='database',
        default=DEFAULT_DB_ALIAS, 
        help='Nominates a specific database to load fixtures into. '
             'Defaults to the "default" database.'
      )
      parser.add_argument(
        '--app', action='store', dest='app_label', default=None,
        help='Only look for fixtures in the specified app.',
      )
      parser.add_argument(
        '--ignorenonexistent', '-i', action='store_true',
        dest='ignore', default=False, help='Ignores entries in the '
            'serialized data for fields that do not currently exist '
            'on the model.'
      )
      parser.add_argument(
        '--format', action='store', dest='format', default=None,
        help='Format of serialized data when reading from stdin.',
      )

    def handle(self, *fixture_labels, **options):
      self.ignore = options['ignore']
      self.using = options['database']
      self.app_label = options['app_label']
      self.verbosity = options['verbosity']
      #self.excluded_models, self.excluded_apps = parse_apps_and_model_labels(options['exclude'])
      self.format = options['format']

      '''
      with transaction.atomic(using=self.using):
          self.loaddata(fixture_labels)

      # Close the DB connection -- unless we're still in a transaction. This
      # is required as a workaround for an  edge case in MySQL: if the same
      # connection is used to create tables, load data, and query, the query
      # can return incorrect results. See Django #7572, MySQL #37735.
      if transaction.get_autocommit(self.using):
          connections[self.using].close()
      '''
      self.loaddata(fixture_labels)

    def loaddata(self, fixture_labels):
        #connection = connections[self.using]
        connection = orm = ORM.get(self.using)

        # Keep a count of the installed objects and fixtures
        self.fixture_count = 0
        self.loaded_object_count = 0
        self.fixture_object_count = 0
        self.models = set()

        self.serialization_formats = serializers.get_public_serializer_formats()
        # Forcing binary mode may be revisited after dropping Python 2 support (see #22399)
        self.compression_formats = {
          None: (open, 'rb'),
          'gz': (gzip.GzipFile, 'rb'),
          'zip': (SingleZipReader, 'r'),
          'stdin': (lambda *args: sys.stdin, None),
        }
        if has_bz2:
          self.compression_formats['bz2'] = (bz2.BZ2File, 'r')

        for fixture_label in fixture_labels:
          if self.find_fixtures(fixture_label):
            break
        else:
          return

        '''
        with connection.constraint_checks_disabled():
            for fixture_label in fixture_labels:
                self.load_label(fixture_label)
        '''
        session = orm.sessionmaker()
        session.close()
        for fixture_label in fixture_labels:
          self.load_label(fixture_label)
        session.commit()

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
        if self.verbosity >= 1:
          if self.fixture_object_count == self.loaded_object_count:
            self.stdout.write(
              "Installed %d object(s) from %d fixture(s)"
              % (self.loaded_object_count, self.fixture_count)
            )
          else:
            self.stdout.write(
              "Installed %d object(s) (of %d) from %d fixture(s)"
              % (self.loaded_object_count, self.fixture_object_count,
                 self.fixture_count))

    def load_label(self, fixture_label):
        """
        Loads fixtures files for a given label.
        """
        #connection = connections[self.using]
        #session = Session(bind=connection.connection)
        session = orm.sessionmaker()
        show_progress = self.verbosity >= 3
        
        logger.info('Loading fixture label: "%s"' % fixture_label)
        identity_map = SortedDict()
        for fixture_file, fixture_dir, fixture_name \
                    in self.find_fixtures(fixture_label):
            logger.info('  Loading fixture: %s' % fixture_file)
            _, ser_fmt, cmp_fmt = self.parse_name(
                    os.path.basename(fixture_file))
            open_method, mode = self.compression_formats[cmp_fmt]
            fixture = open_method(fixture_file, mode)
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
                        (cls, key) = identity_key(instance=obj)
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

            # Warn if the fixture we loaded contains 0 objects.
            if objects_in_fixture == 0:
                warnings.warn(
                    "No fixture data found for '%s'. (File format may be "
                    "invalid.)" % fixture_name, RuntimeWarning
                )

        try:
            updates = get_deferred_updates(session)
            session.flush()

            for cls, filters, update in updates:
                # TODO: fix this, it is terrible, but sqla can't handle the
                # "normal" update method when table inheritance is involved
                # session.query(cls).filter(filters).update(update)
                instance = session.query(cls).filter(filters)
                for attr, value in update.items():
                    setattr(instance, attr.key, value)
            session.flush()
        except:
            session.rollback()
            raise

    def _find_fixtures(self, fixture_label):
        """
        Finds fixture files for a given label.
        """
        fixture_name, ser_fmt, cmp_fmt = self.parse_name(fixture_label)
        databases = [self.using, None]
        cmp_fmts = list(self.compression_formats.keys()) \
                if cmp_fmt is None else [cmp_fmt]
        ser_fmts = serializers.get_public_serializer_formats() \
                if ser_fmt is None else [ser_fmt]

        if os.path.isabs(fixture_name):
            fixture_dirs = [os.path.dirname(fixture_name)]
            fixture_name = os.path.basename(fixture_name)
        else:
            fixture_dirs = self.fixture_dirs
            if os.path.sep in os.path.normpath(fixture_name):
                fixture_dirs = [
                    os.path.join(dir_, os.path.dirname(fixture_name))
                    for dir_ in fixture_dirs]
                fixture_name = os.path.basename(fixture_name)

        suffixes = ('.'.join(ext for ext in combo if ext)
                for combo in product(databases, ser_fmts, cmp_fmts))
        targets = set('.'.join((fixture_name, suffix)) for suffix in suffixes)

        fixture_files = []
        for fixture_dir in fixture_dirs:
            logger.debug("  Checking %s for fixtures..." 
                        % humanize(fixture_dir))
            fixture_files_in_dir = []
            path = os.path.join(fixture_dir, fixture_name)
            for candidate in glob.iglob(glob_escape(path) + '*'):
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

        if not fixture_files:
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
      fixture_dirs = settings.FIXTURE_DIRS
      if len(fixture_dirs) != len(set(fixture_dirs)):
        raise ImproperlyConfigured("settings.FIXTURE_DIRS contains "
                                  "duplicates.")
      for path in get_app_paths():
        app_dir = os.path.join(os.path.dirname(path), 'fixtures')
        if app_dir in fixture_dirs:
          raise ImproperlyConfigured(
            "'%s' is a default fixture directory for the '%s' app "
            "and cannot be listed in settings.FIXTURE_DIRS." 
            % (app_dir, app_label)
          )

        if self.app_label and app_label != self.app_label:
            continue
        if os.path.isdir(app_dir):
          dirs.append(app_dir)
      dirs.extend(list(fixture_dirs))
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

        if len(parts) > 1:
            if parts[-1] in self.serialization_formats:
                ser_fmt = parts[-1]
                parts = parts[:-1]
            else:
                raise CommandError(
                    "Problem installing fixture '%s': %s is not a known "
                    "serialization format." % (''.join(parts[:-1]), parts[-1]))
        else:
            ser_fmt = None

        name = '.'.join(parts)

        return name, ser_fmt, cmp_fmt
