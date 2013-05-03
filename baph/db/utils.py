from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from threading import local

from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError


DEFAULT_DB_ALIAS = 'default'

def django_backend_to_sqla_dialect(backend):
    if backend.find('.') == -1:
        # not a django backend, pass it through
        return backend
    backend = backend.rsplit('.',1)[-1]
    if backend == 'sqlite3':
        return 'sqlite'
    elif backend == 'postgresql_psycopg2':
        return 'postgresql'
    return backend

def create_sqla_engine_url(db_settings={}):
    " converts a dict of django db settings into an sqla url "
    dialect = db_settings.get('DIALECT')
    if not dialect:
        " try to guess from the django ENGINE param "
        try:
            dialect = django_backend_to_sqla_dialect(db_settings['ENGINE'])
        except KeyError:
            raise ImproperlyConfigured('database config must include either ' \
                'a value for either ENGINE or DIALECT')
    url = dialect
    if 'DRIVER' in db_settings:
        url += '+%s' % db_settings['DRIVER']
    url += '://'
    if 'USER' in db_settings and db_settings['USER']:
        url += db_settings['USER']
    if 'PASSWORD' in db_settings and db_settings['PASSWORD']:
        url += ':%s' % db_settings['PASSWORD']
    if 'HOST' in db_settings and db_settings['HOST']:
        url += '@%s' % db_settings['HOST']
    elif dialect in ('mysql','postgresql'):
        url += '@localhost'
    if 'PORT' in db_settings and db_settings['PORT']:
        url += ':%s' % db_settings['PORT']
    if 'NAME' in db_settings:
        url += '/%s' % db_settings['NAME']
    return url

def load_backend(db_settings={}):
    url = create_sqla_engine_url(db_settings)
    try:
        engine = create_engine(url)
        return engine
    except ArgumentError:
        error_msg = "%r isn't a valid dialect/driver" % url
        raise ImproperlyConfigured(error_msg)


class ConnectionHandler(object):
    def __init__(self, databases):
        if not databases:
            self.databases = {
                DEFAULT_DB_ALIAS: {
                    'ENGINE': 'django.db.backends.dummy',
                },
            }
        else:
            self.databases = databases
        for db in self.databases.values():
            if not 'DIALECT' in db:
                db['DIALECT'] = django_backend_to_sqla_dialect(db['ENGINE'])

        self._engines = local()

    def ensure_defaults(self, alias):
        """
        Puts the defaults into the settings dictionary for a given connection
        where no settings is provided.
        """
        try:
            conn = self.databases[alias]
        except KeyError:
            raise ConnectionDoesNotExist("The connection %s doesn't exist" % alias)

        conn.setdefault('ENGINE', 'django.db.backends.dummy')
        if conn['ENGINE'] == 'django.db.backends.' or not conn['ENGINE']:
            conn['ENGINE'] = 'django.db.backends.dummy'
        conn.setdefault('OPTIONS', {})
        #conn.setdefault('TIME_ZONE', 'UTC' if settings.USE_TZ else settings.TIME_ZONE)
        for setting in ['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']:
            conn.setdefault(setting, '')
        for setting in ['TEST_CHARSET', 'TEST_COLLATION', 'TEST_NAME', 'TEST_MIRROR']:
            conn.setdefault(setting, None)

    def __getitem__(self, alias):
        if hasattr(self._engines, alias):
            return getattr(self._engines, alias)

        self.ensure_defaults(alias)
        db = self.databases[alias]
        engine = load_backend(db)
        setattr(self._engines, alias, engine)
        #backend = load_backend(db['ENGINE'])
        #conn = backend.DatabaseWrapper(db, alias)
        #setattr(self._connections, alias, conn)
        return engine

    def __setitem__(self, key, value):
        setattr(self._engines, key, value)

    def __iter__(self):
        return iter(self.databases)

    def all(self):
        return [self[alias] for alias in self]
