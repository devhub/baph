# -*- coding: utf-8 -*-
from __future__ import absolute_import

import gzip
import os.path
import pickle
import time

from django.conf import settings
from django.core.cache.backends.filebased import FileBasedCache


DEFAULT_TIMEOUT = object()

class CustomOpenerFileCache(FileBasedCache):
    '''Allows one to specify a custom opener function to be used when caching
    data into a file.
    '''

    def __init__(self, dir, params, opener=open):
        super(CustomOpenerFileCache, self).__init__(dir, params)
        self._opener = opener

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        fname = self._key_to_file(key)
        try:
            with self._opener(fname, 'rb') as f:
                exp = pickle.load(f)
                now = time.time()
                if exp is not None and exp < now:
                    self._delete(fname)
                else:
                    return pickle.load(f)
        except (IOError, OSError, EOFError, pickle.PickleError):
            pass
        return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        
        fname = self._key_to_file(key)
        dirname = os.path.dirname(fname)

        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout

        self._cull()

        try:
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with self._opener(fname, 'wb') as f:
                expiry = None if timeout is None else time.time() + timeout
                pickle.dump(expiry, f, pickle.HIGHEST_PROTOCOL)
                pickle.dump(value, f, pickle.HIGHEST_PROTOCOL)
        except (IOError, OSError):
            pass

    def has_key(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        fname = self._key_to_file(key)
        try:
            with self._opener(fname, 'rb') as f:
                exp = pickle.load()
            now = time.time()
            if exp < now:
                self._delete(fname)
                return False
            else:
                return True
        except (IOError, OSError, EOFError, pickle.PickleError):
            return False
"""
if hasattr(settings, 'FILE_CACHE_LOCATION'):
    cache = CustomOpenerFileCache(settings.FILE_CACHE_LOCATION,
                                  {'max_entries': 10000},
                                  opener=gzip.open)
else:
    cache = None
"""
