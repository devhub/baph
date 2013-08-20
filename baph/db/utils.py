from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import ConnectionHandler
from threading import local

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool


DEFAULT_DB_ALIAS = 'default'

def django_backend_to_sqla_drivername(backend):
    if backend.find('.') == -1:
        # not a django backend, pass it through
        return backend
    backend = backend.rsplit('.',1)[-1]
    if backend == 'sqlite3':
        return 'sqlite'
    elif backend == 'postgresql_psycopg2':
        return 'postgresql'
    return backend

def django_config_to_sqla_config(config):
    """
    Takes a dict of django db config params and converts the keys
    to be useable by sqla's URL() function. If 'DRIVERNAME' is not present,
    it will attempt to guess based on the value of ENGINE
    """
    drivername = config.get('DRIVERNAME', 
        django_backend_to_sqla_drivername(config['ENGINE']))
    params = {
        'drivername': drivername,
        'username': config.get('USER', None),
        'password': config.get('PASSWORD', None),
        'host': config.get('HOST', None),
        'port': config.get('PORT', None),
        'database': config.get('NAME', None),
        'query': config.get('OPTIONS', None),
        }
    for k, v in params.items():
        if not v:
            del params[k]
    return params

def load_engine(config):
    url = URL(**django_config_to_sqla_config(config))
    try:
        engine = create_engine(url, poolclass=NullPool,
                               echo=getattr(settings, 'BAPH_DB_ECHO', False))
        return engine
    except ArgumentError:
        error_msg = "%r isn't a valid dialect/driver" % url
        raise ImproperlyConfigured(error_msg)


class DatabaseWrapper(object):
    def __init__(self, db, alias):
        from baph.db.models.base import get_declarative_base
        self.db = db
        self.alias = alias
        self.engine = load_engine(db)
        self.Base = get_declarative_base(bind=self.engine)
        self.sessionmaker = scoped_session(sessionmaker(bind=self.engine,
            autoflush=False))

class EngineHandler(ConnectionHandler):
    def __init__(self, databases):
        if not databases:
            self.databases = {
                DEFAULT_DB_ALIAS: {
                    'ENGINE': 'django.db.backends.dummy',
                },
            }
        else:
            self.databases = databases
        self._connections = type('engine', (), {})

    def __getitem__(self, alias):
        return self.get(alias)

    def get(self, alias=None):
        if not alias:
            alias = DEFAULT_DB_ALIAS
        if hasattr(self._connections, alias):
            return getattr(self._connections, alias)
        self.ensure_defaults(alias)
        db = self.databases[alias]
        conn = DatabaseWrapper(db, alias)
        setattr(self._connections, alias, conn)
        return conn
