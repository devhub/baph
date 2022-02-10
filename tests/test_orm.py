# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.db.orm import Mapify, ORM
from baph.test.base import TestCase
from django.conf import settings
from sqlalchemy import Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import clear_mappers
from sqlalchemy.sql import join


class ORMTestCase(TestCase):
    '''Test case for the ORM class.'''

    def test_create_url(self):
        # URLs taken from: http://www.sqlalchemy.org/docs/05/dbengine.html
        test_data = [
            {
                'expected': 'postgres://scott:tiger@localhost/mydatabase',
                'params': {
                    'ENGINE': 'postgres',
                    'USER': 'scott',
                    'PASSWORD': 'tiger',
                    'HOST': 'localhost',
                    'NAME': 'mydatabase',
                },
            },
            {
                'expected': 'postgres://scott@localhost/mydatabase',
                'params': {
                    'ENGINE': 'postgres',
                    'USER': 'scott',
                    'HOST': 'localhost',
                    'NAME': 'mydatabase',
                },
            },
            {
                'expected': 'postgres://scott@localhost/mydatabase',
                'params': {
                    'ENGINE': 'postgres',
                    'USER': 'scott',
                    'PASSWORD': '',
                    'HOST': 'localhost',
                    'NAME': 'mydatabase',
                },
            },
            {
                'expected': 'oracle://scott:tiger@tnsname',
                'params': {
                    'ENGINE': 'oracle',
                    'USER': 'scott',
                    'PASSWORD': 'tiger',
                    'HOST': 'tnsname',
                },
            },
            {
                'expected': 'mssql://mydsn',
                'params': {
                    'ENGINE': 'mssql',
                    'HOST': 'mydsn',
                },
            },
            {
                'expected': 'sqlite:///foo.db',
                'params': {
                    'ENGINE': 'sqlite',
                    'NAME': 'foo.db',
                },
            },
            {
                'expected': 'sqlite:////absolute/path/to/foo.db',
                'params': {
                    'ENGINE': 'sqlite',
                    'NAME': '/absolute/path/to/foo.db',
                },
            },
            {
                'expected': 'sqlite:////absolute/path/to/foo.db',
                'params': {
                    'ENGINE': 'sqlite',
                    'USER': '',
                    'PASSWORD': '',
                    'HOST': '',
                    'NAME': '/absolute/path/to/foo.db',
                },
            },
            {
                'expected': 'sqlite://',
                'params': {
                    'ENGINE': 'sqlite',
                },
            },
        ]
        for data in test_data:
            self.assertEqual(ORM._create_url(data['params']),
                             data['expected'])

    def test_orm_creation(self):
        orm = ORM.get()
        session = orm.sessionmaker()
        result = session.execute('SELECT 1').fetchone()
        self.assertEqual(result, (1,))

    def test_session_close(self):
        # Please fix...this is not very useful IMO. -Mark
        orm = ORM.get()
        session = orm.sessionmaker()
        session.execute('SELECT 1')
        orm.sessionmaker_close()

    def test_session_remove(self):
        # Please fix...this is not very useful IMO. -Mark
        orm = ORM.get()
        session = orm.sessionmaker()
        session.execute('SELECT 1')
        orm.sessionmaker_remove()

    def test_session_rollback(self):
        orm = ORM.get()
        session = orm.sessionmaker()
        sql = 'SELECT col FROM nonexistent_baph_table'
        try:
            result = session.execute(sql).fetchone()
        except SQLAlchemyError:
            orm.sessionmaker_rollback()
        result = session.execute('SELECT 1').fetchone()
        self.assertEqual(result, (1,))


class ReadonlyORMTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        ORM._database = None
        settings.DATABASES['default']['READONLY_NAME'] = '/tmp/test-baph-ro.db'

    @classmethod
    def tearDownClass(cls):
        ORM._database = None

    def test_readonly_orm_creation(self):
        orm = ORM.get()
        session = orm.sessionmaker()
        result = session.execute('SELECT 1').fetchone()
        self.assertEqual(result, (1,))
        session = orm.sessionmaker(readonly=True)
        result = session.execute('SELECT 1').fetchone()
        self.assertEqual(result, (1,))

    def test_readonly_session_close(self):
        # Please fix...this is not very useful IMO. -Mark
        orm = ORM.get()
        session = orm.sessionmaker(readonly=True)
        session.execute('SELECT 1')
        orm.sessionmaker_close()

    def test_readonly_session_remove(self):
        # Please fix...this is not very useful IMO. -Mark
        orm = ORM.get()
        session = orm.sessionmaker(readonly=True)
        session.execute('SELECT 1')
        orm.sessionmaker_remove()

    def test_readonly_session_rollback(self):
        orm = ORM.get()
        session = orm.sessionmaker(readonly=True)
        sql = 'SELECT col FROM nonexistent_baph_table'
        try:
            result = session.execute(sql).fetchone()
        except SQLAlchemyError:
            orm.sessionmaker_rollback()
        result = session.execute('SELECT 1').fetchone()
        self.assertEqual(result, (1,))


class MapifiableClass(object):
    '''Class used to test the Mapify class decorator.'''


class MapifyTestCase(TestCase):
    '''Test case for the Mapify class decorator.'''

    @classmethod
    def setUpClass(cls):
        ORM._database = None
        cls.orm = ORM.get()
        cls.session = cls.orm.sessionmaker()
        cls.session.execute('''\
CREATE TABLE test_baph_mapify (
    id INTEGER PRIMARY KEY,
    string VARCHAR(16),
    number_with_decimal_point REAL(10)
);''')
        cls.session.execute('''\
CREATE TABLE test_baph_mapify_join (
    foreign_key INTEGER PRIMARY KEY REFERENCES test_baph_mapify(id),
    other_string VARCHAR(16)
);''')

    @classmethod
    def tearDownClass(cls):
        cls.session.execute('DROP TABLE test_baph_mapify')
        cls.session.execute('DROP TABLE test_baph_mapify_join')
        cls.orm.sessionmaker_close()
        cls.orm.sessionmaker_remove()
        ORM._database = None

    def setUp(self):
        clear_mappers()

    def assertHasAttr(self, obj_or_cls, attr):
        self.assertTrue(hasattr(obj_or_cls, attr))

    def test_mapify_with_table_name(self):
        TableName = Mapify(self.orm, 'test_baph_mapify')(MapifiableClass)
        self.assertHasAttr(TableName, '__table__')
        self.assertHasAttr(TableName, 'id')
        self.assertHasAttr(TableName, 'string')
        self.assertHasAttr(TableName, 'number_with_decimal_point')

    def test_mapify_with_table_object(self):
        table = Table('test_baph_mapify', self.orm.metadata, useexisting=True)
        TableObj = Mapify(self.orm, table)(MapifiableClass)
        self.assertHasAttr(TableObj, '__table__')
        self.assertHasAttr(TableObj, 'id')
        self.assertHasAttr(TableObj, 'string')
        self.assertHasAttr(TableObj, 'number_with_decimal_point')

    def test_mapify_with_table_object_join(self):
        t1 = Table('test_baph_mapify', self.orm.metadata, useexisting=True)
        t2 = Table('test_baph_mapify_join', self.orm.metadata, autoload=True,
                   useexisting=True)
        tjoin = join(t1, t2)
        JoinObj = Mapify(self.orm, tjoin)(MapifiableClass)
        self.assertHasAttr(JoinObj, '__table__')
        self.assertHasAttr(JoinObj, 'id')
        self.assertHasAttr(JoinObj, 'string')
        self.assertHasAttr(JoinObj, 'number_with_decimal_point')
        self.assertHasAttr(JoinObj, 'other_string')
