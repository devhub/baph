from django.conf import settings
from django.core import signals
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import (ConnectionRouter,
    DatabaseError, IntegrityError)
from sqlalchemy.orm import scoped_session, sessionmaker

from baph.db.utils import EngineHandler, DEFAULT_DB_ALIAS


__all__ = ('ORM', 'DEFAULT_DB_ALIAS', 'engines', 'EngineHandler',
    'DatabaseError', 'IntegrityError', )
# 'connection', 'connections', 'router', 

ORM = EngineHandler(settings.DATABASES)

# TODO: implement routing
#router = ConnectionRouter()

#connection = DefaultConnectionProxy()

