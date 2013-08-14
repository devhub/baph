from baph.db.utils import ConnectionHandler, load_backend, DEFAULT_DB_ALIAS
from django.conf import settings
from django.core import signals
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import (ConnectionRouter,
    DatabaseError, IntegrityError)
from sqlalchemy.orm import scoped_session, sessionmaker

__all__ = ('backend', 'connection', 'connections', 'router', 'DatabaseError',
    'IntegrityError', 'DEFAULT_DB_ALIAS')


if settings.DATABASES and DEFAULT_DB_ALIAS not in settings.DATABASES:
    raise ImproperlyConfigured("You must define a '%s' database" \
        % DEFAULT_DB_ALIAS)

connections = ConnectionHandler(settings.DATABASES)

router = ConnectionRouter(settings.DATABASE_ROUTERS)

class DefaultConnectionProxy(object):
    """
    Proxy for accessing the default DatabaseWrapper object's attributes. If you
    need to access the DatabaseWrapper object itself, use
    connections[DEFAULT_DB_ALIAS] instead.
    """
    def __getattr__(self, item):
        return getattr(connections[DEFAULT_DB_ALIAS], item)

    def __setattr__(self, name, value):
        return setattr(connections[DEFAULT_DB_ALIAS], name, value)

connection = DefaultConnectionProxy()
engine = connections[DEFAULT_DB_ALIAS]
Session = scoped_session(sessionmaker(bind=engine))

#
#print connections['default']
#print dir(connections['default'])
#sys.exit()
#backend = load_backend(connection.settings_dict['ENGINE'])

