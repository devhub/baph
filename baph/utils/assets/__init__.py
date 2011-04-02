# -*- coding: utf-8 -*-
'''\
:mod:`baph.utils.assets` -- Static Asset Management
===================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

``django-admin`` Commands
-------------------------

.. django-admin:: deploy-css

Minifies, compresses, and deploys CSS files specified in :setting:`CSS_FILES`
to Amazon S3. Requires `cssutils`_, :setting:`MEDIA_ROOT`,
:setting:`MEDIA_URL`, and :setting:`AWS_STORAGE_BUCKET_NAME`.

.. _cssutils: http://cthedot.de/cssutils/

.. django-admin:: deploy-js

Minifies, compresses, and deploys JS files specified in :setting:`JS_FILES`
to Amazon S3. Requires the `Google Closure Compiler`_, :setting:`MEDIA_ROOT`,
and :setting:`AWS_STORAGE_BUCKET_NAME`.

Use the :djadminopt:`--closure` option to specify the absolute path of the
Google Closure compiler jar file. If not provided, the default is
``/var/lib/google-closure/compiler.jar``.

.. _Google Closure Compiler: https://code.google.com/p/closure-compiler/

.. django-admin:: deploy-static

An extension of :djadmin:`collectstatic` from `django-staticfiles`_. This does
not handle CSS files or unminified JavaScript files, as they are expected to
be handled by :djadmin:`deploy-css` and :djadmin:`deploy-js`, respectively.

.. _django-staticfiles: https://github.com/jezdez/django-staticfiles

Available Settings
------------------

.. setting:: CSS_FILES
.. setting:: JS_FILES
.. setting:: STATIC_FILES

``CSS_FILES``, ``JS_FILES``, ``STATIC_FILES``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All of these settings are dictionaries, where the keys are paths to the files,
and the values are the latest git revisions associated with the files. In the
cases of ``CSS_FILES`` and ``JS_FILES``, the key omits the extension (including
the period).

Functions
---------
'''

from ..importing import import_attr
import gzip
import os
from subprocess import PIPE, Popen

StringIO = import_attr(['cStringIO', 'StringIO'], 'StringIO')

GIT_LOG = ['git', 'log', '--format=oneline', '-1']


def get_git_revision(filename):
    '''Retrieves the latest git revision of a given filename, or None if it's
    not versioned.
    '''
    last_rev = None
    cwd = os.path.dirname(filename)
    # check git for last revision
    pipe = Popen(GIT_LOG + [filename], cwd=cwd, stdout=PIPE, stderr=PIPE)
    retcode = pipe.wait()
    if retcode == 0:
        # store last revision in a file.
        last_rev = pipe.stdout.read().split(' ', 1)[0]
    return last_rev


def get_git_revision_for_files(files):
    '''Retrieves the latest git revision for a given list of files, or None if
    none of the files are versioned.
    '''
    last_rev = None
    cwd = os.path.dirname(files[0])
    # check git for last revision
    pipe = Popen(GIT_LOG + ['--'] + list(files), cwd=cwd, stdout=PIPE,
                 stderr=PIPE)
    retcode = pipe.wait()
    if retcode == 0:
        last_rev = pipe.stdout.read().split(' ', 1)[0]
        if last_rev == '':
            last_rev = None
    return last_rev


def gzip_data(content):
    gzio = StringIO()
    gz = gzip.GzipFile(mode='wb', fileobj=gzio)
    gz.write(content)
    gz.close()
    return gzio
