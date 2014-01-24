# -*- coding: utf-8 -*-
'''\
:mod:`baph.db.types` -- Custom SQLAlchemy Types
===============================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
.. moduleauthor:: Gerald Thibault <jt@evomediagroup.com>
'''
try:
    import json
except ImportError:
    import simplejson as json
import datetime
import uuid
import re

from django.conf import settings
from django.utils.timezone import is_naive, is_aware, make_aware
from pytz import timezone
from sqlalchemy import types
from sqlalchemy.databases import mysql, postgresql
from sqlalchemy.ext.mutable import Mutable


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

# http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html

class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()

class Dict(JsonText):

    @property
    def python_type(self):
        return dict

class TZAwareDateTime(types.TypeDecorator):
    impl = types.DateTime

    def __init__(self, tz, *args, **kwargs):
        super(TZAwareDateTime, self).__init__(*args, **kwargs)
        self.tz = timezone(tz)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, basestring):
            value = value.replace('T', ' ').replace('Z', '+00:00')
            p = re.compile('([0-9: -]+)\.?([0-9]*)([\+-][0-9]{2}:?[0-9]{2})?')
            dt, ms, tz = p.match(value).groups()
            value = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            if tz:
                pol, h, m = tz[0], int(tz[1:3]), int(tz[-2:])
                delta = datetime.timedelta(hours=h, minutes=m)
                if pol == '+':
                    value -= delta
                else:
                    value += delta

        if is_naive(value):
            value = make_aware(value, self.tz)
        else:
            value = value.replace(tzinfo=self.tz)
        return value.strftime('%Y-%m-%d %H:%M:%S')

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        value = self.tz.localize(value, is_dst=None)
        return value
        
    def compare_values(self, x, y):
        if x and y and is_naive(x) and is_aware(y):
            x = make_aware(x, self.tz)
        elif x and y and is_aware(x) and is_naive(y):
            y = make_aware(y, self.tz)
        return x == y
