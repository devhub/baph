# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.db.orm import ORM
from baph.decorators.db import sqlalchemy_session
from baph.test.base import TestCase


@sqlalchemy_session
def passthrough(session=None):
    '''Test docstring.'''
    return session


class DBDecoratorsTestCase(TestCase):
    '''Tests :mod:`baph.decorators.db`.'''

    @classmethod
    def setUpClass(cls):
        cls.orm = ORM.get()

    def test_sqlalchemy_session(self):
        session = self.orm.sessionmaker()
        self.assertEqual(passthrough(session=session), session)
        self.orm.sessionmaker_remove()
        self.assertIsNotNone(passthrough())
        self.assertNotEqual(passthrough(), session)

        self.assertEqual(passthrough.__doc__, 'Test docstring.')
