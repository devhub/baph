# -*- coding: utf-8 -*-
'''\
:mod:`baph.sessions.backends.memcache` -- Memcached Session Backend
===================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase, CreateError
from newcache import CacheClass


class Cache(CacheClass):

    def __init__(self, server, params):
        super(Cache, self).__init__('', params)
        self._servers = server


class SessionStore(SessionBase):
    '''A memcached-based session store. Useful if you wish to use memcached as
    the session backend, but another cache method for general caching.

    This backend requires `django-newcache`_, and one of the following
    memcache libraries:

    * `pylibmc`_ (recommended)
    * `python-memcached`_

    .. _django-newcache: http://github.com/ericflo/django-newcache
    .. _pylibmc: http://pypi.python.org/pypi/pylibmc
    .. _python-memcached: http://pypi.python.org/pypi/python-memcached

    To use:

    * Set ``SESSION_ENGINE`` in ``settings.py`` to
      ``baph.sessions.backends.memcache``.
    * Set ``SESSION_MEMCACHE_SERVERS`` in ``settings.py`` to a list of one or
      more memcache servers that will be used.
    * If necessary, set the ``SESSION_MEMCACHE_SETTINGS`` variable in
      ``settings.py``. This is a dictionary populated with settings such as
      ``max_entries``.
    '''

    def __init__(self, session_key=None):
        session_memcache_settings = getattr(settings,
                                            'SESSION_MEMCACHE_SETTINGS',
                                            {})
        self._cache = Cache(settings.SESSION_MEMCACHE_SERVERS,
                            session_memcache_settings)
        super(SessionStore, self).__init__(session_key)

    def load(self):
        session_data = self._cache.get(self.session_key)
        if session_data is not None:
            return session_data
        self.create()
        return {}

    def create(self):
        # Because a cache can fail silently (e.g. memcache), we don't know if
        # we are failing to create a new session because of a key collision or
        # because the cache is missing. So we try for a (large) number of times
        # and then raise an exception. That's the risk you shoulder if using
        # cache backing.
        for i in xrange(10000):
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return
        raise RuntimeError("Unable to create a new session key.")

    def save(self, must_create=False):
        if must_create:
            func = self._cache.add
        else:
            func = self._cache.set
        result = func(self.session_key, self._get_session(no_load=must_create),
                self.get_expiry_age())
        if must_create and not result:
            raise CreateError

    def exists(self, session_key):
        return session_key in self._cache

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        self._cache.delete(session_key)
