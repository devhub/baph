# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.db.models import Model
from baph.db.orm import ORM
from baph.db.types import UUID
from baph.test.base import TestCase
from sqlalchemy import Column
import uuid

orm = ORM.get()


class UUIDModel(orm.Base, Model):
    '''Test model for the UUID column type.'''
    __tablename__ = 'test_baph_uuid_model'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)


class NullableUUIDModel(orm.Base, Model):
    '''Test model for the UUID column type.'''
    __tablename__ = 'test_baph_nullable_uuid_model'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    uuid = Column(UUID, nullable=True)


class UUIDTestCase(TestCase):
    '''Tests the UUID column type for SQLAlchemy.'''

    @classmethod
    def setUpClass(cls):
        UUIDModel.__table__.create()
        NullableUUIDModel.__table__.create()

    def setUp(self):
        self.session = orm.sessionmaker()

    def tearDown(self):
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        NullableUUIDModel.__table__.drop()
        UUIDModel.__table__.drop()

    def test_add_row(self):
        row = UUIDModel()
        self.session.add(row)
        self.session.commit()
        self.assertIsInstance(row.id, uuid.UUID)

    def test_get_row(self):
        row = UUIDModel()
        self.session.add(row)
        self.session.commit()
        row_id = row.id
        model = self.session.query(UUIDModel) \
                            .get(row_id)
        self.assertIsNotNone(model)
        self.assertEqual(model.id, row_id)

    def test_update_row(self):
        row = UUIDModel()
        self.session.add(row)
        self.session.commit()
        new_uuid = uuid.uuid4()
        row.id = new_uuid
        self.session.commit()
        model = self.session.query(UUIDModel) \
                            .get(new_uuid)
        self.assertIsNotNone(model)
        self.assertEqual(model.id, new_uuid)

    def test_none_value(self):
        row = NullableUUIDModel(uuid=None)
        self.session.add(row)
        self.session.commit()
        model = self.session.query(NullableUUIDModel) \
                            .get(row.id)
        self.assertIsNotNone(model)
        self.assertIsNone(model.uuid)

    def test_invalid_value(self):
        for value in ['hello', u'hello', 1, 1.0, True, object()]:
            row = UUIDModel(id=value)
            self.session.add(row)
            self.assertRaises(ValueError, self.session.commit)
            self.session.rollback()
