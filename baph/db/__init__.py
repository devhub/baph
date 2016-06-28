from django.conf import settings
from django.core import signals
from django.core.exceptions import ImproperlyConfigured
from django.db import (ConnectionHandler, ConnectionRouter,
                       DefaultConnectionProxy, DatabaseError, IntegrityError)

from baph.db.utils import EngineHandler, DEFAULT_DB_ALIAS


__all__ = ('ORM', 'DEFAULT_DB_ALIAS', 'engines', 'EngineHandler',
    'DatabaseError', 'IntegrityError', )
# 'connection', 'connections', 'router', 

ORM = EngineHandler(settings.DATABASES)

connections = ConnectionHandler()

router = ConnectionRouter()

connection = DefaultConnectionProxy()
