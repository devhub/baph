# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf import settings
from django.core.files import File
from gzip import GzipFile
from optparse import make_option
import os.path
import pickle
from staticfiles.management.commands import collectstatic
from ....importing import import_attr
from ... import css, get_git_revision, gzip_data, js

StringIO = import_attr(['cStringIO', 'StringIO'], 'StringIO')

CLOSURE_COMPILER_JAR = '/var/lib/google-closure/compiler.jar'
REVISION_FILE_NAME = '.file_table.pickle.gz'


class SIOFile(File):
    def __init__(self, content):
        super(SIOFile, self).__init__(content)
        self.size = len(content.getvalue())

    def __str__(self):
        return 'StringIO-based File'

    def _get_name(self):
        return '<%s>' % str(self)

    def _set_name(self, name):
        pass

    name = property(_get_name, _set_name)

    def __nonzero__(self):
        return True

    def open(self, mode=None):
        self.seek(0)

    def write(self, content):
        super(SIOFile, self).write(content)
        self.size = len(self.file.getvalue())

    def close(self):
        pass


class Command(collectstatic.Command):
    help = u'Collects static files from apps and other locations to a ' \
           u'single location, and maintains a dictionary of files and '\
           u'revisions.'

    option_list = collectstatic.Command.option_list + (
        make_option('--closure', default=CLOSURE_COMPILER_JAR, dest='closure',
            help=u'The absolute path of the Google Closure compiler jar ' \
                 u'used to minify the JavaScript',
            metavar='JAR_PATH'),
    )

    requires_model_validation = False

    REASON_NOT_VERSIONED = 100
    REASON_MINIFIED = 101
    REASONS = collectstatic.Command.REASONS
    REASONS.update({
        REASON_NOT_VERSIONED: 'not versioned',
        REASON_MINIFIED: 'already in a minified file',
    })

    def verbose(self, msg, verbosity=2):
        if self._verbosity >= verbosity:
            self.stdout.write('%s\n' % msg)

    def handle_noargs(self, **options):
        self._options = options
        if self.destination_storage.exists(REVISION_FILE_NAME):
            try:
                remote_file = self.destination_storage.open(REVISION_FILE_NAME)
                pgz = GzipFile(fileobj=remote_file)
                self._file_dict = pickle.loads(pgz.read())
            except EOFError:
                self._file_dict = {}
        else:
            self._file_dict = {}

        super(Command, self).handle_noargs(**options)

        if not self._dry_run:
            pickledgz = SIOFile(gzip_data(pickle.dumps(self._file_dict)))
            self.destination_storage.delete(REVISION_FILE_NAME)
            self.destination_storage.save(REVISION_FILE_NAME, pickledgz)

    def file_status(self, source_storage, source, prefix, destination):
        status, detail = super(Command, self).file_status(source_storage,
                                                          source, prefix,
                                                          destination)
        if status == self.STATUS_COPY:
            changed = False
            last_rev = get_git_revision(source_storage.path(source))
            base, ext = os.path.splitext(source)
            if last_rev:
                self.verbose(' + "%s" in git, last revision: %s' % \
                             (source, last_rev))
                key = os.path.join(prefix, source)
                if self._file_dict.get(key) == last_rev:
                    return self.STATUS_SKIP, self.REASON_NOT_MODIFIED
                self._file_dict[key] = last_rev
                if ext == '.js' and not base.endswith('.min'):
                    detail = self.minify(source_storage, base, ext, js)
                elif ext == '.css':
                    if base in settings.CSS_FILES:
                        detail = self.minify(source_storage, base, ext, css)
                    else:
                        return self.STATUS_SKIP, self.REASON_MINIFIED
            else:
                return self.STATUS_SKIP, self.REASON_NOT_VERSIONED
        return status, detail

    def minify(self, source_storage, base, ext, minifier):
        original = '%s%s' % (base, ext)
        src = source_storage.open(original)
        if self._dry_run:
            self.verbose('Pretending to minify "%s"' % original)
            output = None
        else:
            output = SIOFile(StringIO())
            self.verbose('Minifying "%s" to "%s"' % (original, output.name),
                         verbosity=1)
            minifier.minify(src, output, **self._options)
        return output
