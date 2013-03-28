# -*- coding: utf-8 -*-
'''\
:mod:`baph.db.types` -- Custom SQLAlchemy Types
===============================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''
try:
    import json
except ImportError:
    import simplejson as json
import uuid

from sqlalchemy import types
from sqlalchemy.databases import mysql, postgresql


class UUID(types.TypeDecorator):
    '''Generic UUID column type for SQLAlchemy. Includes native support for
    PostgreSQL and a MySQL-specific implementation, in addition to the
    ``CHAR``-based fallback. Based on code from the following sources:

    * http://blog.sadphaeton.com/2009/01/19/sqlalchemy-recipeuuid-column.html
    * http://article.gmane.org/gmane.comp.python.sqlalchemy.user/24056
    '''
    impl = types.CHAR

    def __init__(self):
        # use the char's length here
        super(UUID, self).__init__(length=36)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.MSBinary(16))
        elif dialect.name in ('postgres', 'postgresql'):
            return dialect.type_descriptor(postgresql.PGUuid())
        else:
            return dialect.type_descriptor(types.CHAR(self.impl.length))

    def process_bind_param(self, value, dialect=None):
        if value:
            if isinstance(value, uuid.UUID):
                if dialect:
                    if dialect.name == 'mysql':
                        return value.bytes
                    elif dialect.name in ('postgres', 'postgresql'):
                        return value
                return str(value)
            else:
                raise ValueError('value %s is not a valid uuid.UUID' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):
        if value:
            if dialect:
                if dialect.name == 'mysql':
                    return uuid.UUID(bytes=value)
                elif dialect.name in ('postgres', 'postgresql'):
                    return value
            return uuid.UUID(value)
        else:
            return None

    def is_mutable(self):
        return False
        

class Json(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if not value:
            return None
        return json.loads(value)

JsonType = Json

class JsonText(JsonType):
    impl = types.UnicodeText

class List(JsonText):

    @property
    def python_type(self):
        return list

class Dict(JsonText):

    @property
    def python_type(self):
        return dict
