# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.db.models import CustomPropsModel, Model
from baph.db.orm import ORM
from baph.test.base import TestCase
from sqlalchemy import Column, Integer, String, Unicode
from sqlalchemy.orm import synonym
import six

orm = ORM.get()


class TestModel(orm.Base, Model):
    '''Test model used by the test case.'''
    __tablename__ = 'test_baph_model'

    id = Column(Integer, primary_key=True)
    str_col = Column(String(10))
    unicode_col = Column(Unicode(10))


class TestModelWithProp(orm.Base, Model):
    '''Test model (with an extra property) used by the test case.'''
    __tablename__ = 'test_baph_model_with_prop'

    id = Column(Integer, primary_key=True)
    str_col = Column(String(10))

    @property
    def unicode_col(self):
        return six.text_type(self.str_col)

    def to_dict(self):
        result = super(TestModelWithProp, self).to_dict()
        result['unicode_col'] = self.unicode_col
        return result


class TestCustomPropsModel(orm.Base, CustomPropsModel):
    '''Test model used by the CustomPropsModel test case.'''
    __tablename__ = 'test_baph_custom_props_model'

    id = Column(Integer, primary_key=True)
    _int_col = Column('int_col', Integer, nullable=False)

    def _get_int_col(self):
        return self._int_col - 1

    def _set_int_col(self, value):
        self._int_col = value + 1

    int_col = synonym('_int_col', descriptor=property(_get_int_col,
                                                      _set_int_col))


class ModelTestCase(TestCase):
    '''Tests :class:`baph.db.models.Model`.'''

    @classmethod
    def setUpClass(cls):
        TestModel.__table__.create()
        TestModelWithProp.__table__.create()

    @classmethod
    def tearDownClass(cls):
        TestModelWithProp.__table__.drop()
        TestModel.__table__.drop()

    def setUp(self):
        self.session = orm.sessionmaker()

    def tearDown(self):
        self.session.close()

    def test_add_row(self):
        # Without params
        row = TestModel()
        self.session.add(row)
        self.session.commit()
        self.assertGreater(row.id, 0)
        self.assertIsNone(row.str_col)
        self.assertIsNone(row.unicode_col)

        # With params
        row2 = TestModel(str_col='hello', unicode_col=u'world')
        self.session.add(row2)
        self.session.commit()
        self.assertGreater(row2.id, 0)
        self.assertEqual(row2.str_col, 'hello')
        self.assertEqual(row2.unicode_col, u'world')

    def test_to_dict(self):
        row = TestModel(str_col='one', unicode_col=u'two')
        self.session.add(row)
        self.session.commit()
        values = row.to_dict()
        self.assertGreater(len(values), 0)
        self.assertGreater(values['id'], 0)
        self.assertEqual(values['str_col'], 'one')
        self.assertEqual(values['unicode_col'], u'two')

        row = TestModelWithProp(str_col='three')
        self.session.add(row)
        self.session.commit()
        values = row.to_dict()
        self.assertGreater(len(values), 0)
        self.assertGreater(values['id'], 0)
        self.assertEqual(values['str_col'], 'three')
        self.assertEqual(values['unicode_col'], u'three')

    def test_update(self):
        row = TestModel(str_col='old', unicode_col=u'ancient')
        self.session.add(row)
        self.session.commit()
        self.assertEqual(row.str_col, 'old')
        self.assertEqual(row.unicode_col, u'ancient')
        row.update({
            'str_col': 'new',
            'unicode_col': u'shiny',
        })
        self.session.commit()
        row2 = self.session.query(TestModel).get(row.id)
        self.assertEqual(row2.str_col, 'new')
        self.assertEqual(row2.unicode_col, u'shiny')

    def test_unicode_truncation(self):
        row = TestModel(unicode_col=u'123456789\xc2')
        self.assertEqual(len(row.unicode_col), 9)

    def test_rtl_termination(self):
        '''Ensures that RTL Unicode text is reset to LTR at the end.'''
        # "Advertising Programs" in Arabic, from Google Saudi Arabia
        text = u'البرنامج الإعلاني'
        row = TestModel(unicode_col=text)
        self.assertLess(len(row.unicode_col), len(text))
        ltr = u'\u200e'
        self.assertTrue(row.unicode_col.endswith(ltr))
        sltr = ltr.encode('utf8')
        str_val = row.unicode_col.encode('utf8')
        self.assertLessEqual(len(str_val), 10)
        self.assertTrue(str_val.endswith(sltr))


class CustomPropsModelTestCase(TestCase):
    '''Tests :class:`baph.db.models.CustomPropsModel`.'''

    @classmethod
    def setUpClass(cls):
        TestCustomPropsModel.__table__.create()

    @classmethod
    def tearDownClass(cls):
        TestCustomPropsModel.__table__.drop()

    def setUp(self):
        self.session = orm.sessionmaker()

    def tearDown(self):
        self.session.close()

    def test_custom_prop(self):
        row = TestCustomPropsModel(int_col=1)
        self.session.add(row)
        self.session.commit()
        self.assertGreater(row.id, 0)
        self.assertEqual(row.int_col, 1)
        self.assertEqual(row._int_col, 2)
        values = row.to_dict()
        self.assertIn('int_col', values)
        self.assertNotIn('_int_col', values)
        self.assertEqual(values['int_col'], 1)
