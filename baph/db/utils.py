from django.conf import settings
from django.db.utils import ConnectionHandler


DEFAULT_DB_ALIAS = 'default'

def is_transactional_test():
    return (getattr(settings, 'IS_TEST', False) &
            getattr(settings, 'USE_TRANSACTIONS', False))

def get_tablename(obj):
    if hasattr(obj, '__table__'):
        " this is a class "
        table = obj.__table__
        schema = table.schema or obj.metadata.bind.url.database
        name = table.name
    elif hasattr(obj, 'schema'):
        " this is a table "
        schema = obj.schema or obj.metadata.bind.url.database
        name = obj.name
    else:
        return None
    return '%s.%s' % (schema, name)


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
        from baph.db.backends import DatabaseWrapper
        self.ensure_defaults(alias)
        db = self.databases[alias]
        conn = DatabaseWrapper(db, alias)
        setattr(self._connections, alias, conn)
        return conn
