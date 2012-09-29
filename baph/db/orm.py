# -*- coding: utf-8 -*-
'''\
:mod:`baph.db.orm` -- SQLAlchemy ORM Utilities
==============================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

'''

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_str
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy.sql.expression import Join
import urllib
from urlparse import urlunparse


class ORM(object):
    '''A wrapper class for dealing with the various aspects of SQLAlchemy.

    :param str name: The database settings to use. Defaults to ``default``.

    :ivar Base: The base class for declarative ORM objects.
    :ivar engine: The SQLAlchemy engine.
    :ivar metadata: The SQLAlchemy metadata object.
    '''
    _databases = {}

    def __init__(self, name=None):
        if not name:
            name = 'default'
        data = {}
        if hasattr(settings, 'DATABASES') and \
           name in settings.DATABASES:
            data = settings.DATABASES[name]
        if data.get('ENGINE', '') == '':
            raise ImproperlyConfigured('''\
The database ORM connection requires, at minimum, an engine type.''')
        if '.' in data['ENGINE']:
            data['ENGINE'] = data['ENGINE'].rsplit('.', 1)[-1]

        # django needs sqlite3 but sqlalchemy references sqlite
        if data['ENGINE'] == 'sqlite3':
            data['ENGINE'] = 'sqlite'
        elif data['ENGINE'] == 'postgresql_psycopg2':
            data['ENGINE'] = 'postgresql'

        self.engine = self._create_engine(data)
        ro_values = dict([(k[9:], v) for k, v in data.iteritems()
                             if k.startswith('READONLY_')])
        if len(ro_values):
            ro_data = dict(data)
            ro_data.update(ro_values)
            self.readonly_engine = self._create_engine(ro_data)
        self.metadata = MetaData(self.engine)
        self.Base = declarative_base(metadata=self.metadata)
        if hasattr(self, 'readonly_engine'):
            self._readonly_sessionmaker = \
                scoped_session(sessionmaker(bind=self.readonly_engine))
        self._sessionmaker = scoped_session(sessionmaker(bind=self.engine))

    @staticmethod
    def _create_url(data):
        netloc = ''
        if data.get('USER', '') != '':
            netloc = data['USER']
            if data.get('PASSWORD', '') != '':
                netloc += ':%s' % data['PASSWORD']
            if data.get('HOST', '') != '':
                netloc += '@%s' % data['HOST']
            else:
                netloc += '@localhost'
            if data.get('PORT', '') != '':
                netloc += ':%s' % data['PORT']
        elif data.get('HOST', '') != '':
            netloc = data['HOST']
        url_parts = (data['ENGINE'], netloc, data.get('NAME', ''), '', '', '')
        if url_parts == (data['ENGINE'], '', '', '', '', ''):
            result = '%s://' % data['ENGINE']
        elif 'NAME' in data and url_parts == (data['ENGINE'], '',
                                              data['NAME'], '', '', ''):
            name = urllib.quote(smart_str(data['NAME']))
            result = '%s:///%s' % (data['ENGINE'], name)
        else:
            result = urlunparse(url_parts)
        return result

    @classmethod
    def _create_engine(cls, data):
        '''Creates an SQLAlchemy engine.'''
        return create_engine(cls._create_url(data), convert_unicode=True,
                             encoding='utf8', poolclass=NullPool)

    @classmethod
    def get(cls, name=None):
        '''Singleton method for the :class:`ORM` object.

        :rtype: :class:`ORM`
        '''
        if not name:
            name = 'default'
        db = cls._databases.get(name)
        if not db:
            db = cls._databases[name] = ORM(name=name)
        return db

    def get_existing_table(self, name, *args, **kwargs):
        '''Creates a Table object from an existing SQL table.

        :param str name: The name of the table.
        :param \*args: Extra arguments to pass to
                       :class:`~sqlalchemy.schema.Table`.
        :param \*\*kwargs: Extra keyworded arguments to pass to
                           :class:`~sqlalchemy.schema.Table`.
        :rtype: :class:`sqlalchemy.schema.Table`
        '''
        return Table(name, self.metadata, autoload=True, *args, **kwargs)

    def sessionmaker(self, readonly=False, **kwargs):
        '''Creates an SQLAlchemy session.

        :param bool readonly: Whether to create a session using the read-only
                              settings.
        :rtype: :class:`sqlalchemy.orm.session.Session`
        '''
        if readonly and hasattr(self, '_readonly_sessionmaker'):
            maker = self._readonly_sessionmaker
        else:
            maker = self._sessionmaker
        return maker(**kwargs)

    def sessionmaker_remove(self):
        '''See :meth:`sqlalchemy.orm.session.Session.remove`.'''
        if hasattr(self, '_readonly_sessionmaker'):
            self._readonly_sessionmaker.remove()
        self._sessionmaker.remove()

    def sessionmaker_close(self):
        '''See :meth:`sqlalchemy.orm.session.Session.close`.'''
        if hasattr(self, '_readonly_sessionmaker'):
            self._readonly_sessionmaker.close()
        self._sessionmaker.close()

    def sessionmaker_rollback(self):
        '''See :meth:`sqlalchemy.orm.session.Session.rollback`.'''
        if hasattr(self, '_readonly_sessionmaker'):
            self._readonly_sessionmaker.rollback()
        self._sessionmaker.rollback()


class Mapify(object):
    '''Automatically maps an object to a database table.
    Use as a decorator (Python >= 2.6 only).

    :param orm: The ORM object associated with the table.
    :type orm: :class:`ORM`
    :param table: The table to associate with the object.
    :type table: :class:`str` (table name),
                 :class:`sqlalchemy.sql.expression.Join`, or
                 :class:`sqlalchemy.schema.Table`
    :param \*args: Extra arguments to pass to Table (or the mapper, if table
                   is not a string).
    :param \*\*kwargs: Extra keyworded arguments to pass to Table (or the
                       mapper, if ``table`` is not a string).
    '''

    def __init__(self, orm, table, *args, **kwargs):
        if isinstance(table, (Join, Table)):
            self.table = table
            self.args = args
            self.kwargs = kwargs
        else:
            # assume table name
            self.table = orm.get_existing_table(table, *args, **kwargs)
            self.args = []
            self.kwargs = {}

    def __call__(self, obj):
        obj.__mapper__ = mapper(obj, self.table, *self.args, **self.kwargs)
        obj.__table__ = self.table
        return obj
