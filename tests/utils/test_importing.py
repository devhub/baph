# -*- coding: utf-8 -*-

from baph.utils.importing import (
    import_all_attrs, import_any_attr, import_any_module, import_attr)
from baph.test.base import TestCase
from django.utils.importlib import import_module


class ImportUtilsTestCase(TestCase):
    '''Tests the import-related utility functions.'''

    def test_import_any_module(self):
        expected = import_module('math')
        actual = import_any_module(['invalid_one', 'math'])
        self.assertEqual(actual, expected)
        self.assertRaises(ImportError, import_any_module,
                          ['invalid_one', 'invalid_2'])
        invalid = import_any_module(['invalid_one', 'invalid_2'],
                                    raise_error=False)
        self.assertIsNone(invalid)

    def test_import_attr(self):
        math = import_module('math')

        # valid module and attr
        actual = import_attr(['invalid_one', 'math'], 'pi')
        self.assertEqual(actual, math.pi)

        # invalid modules
        self.assertRaises(ImportError, import_attr,
                          ['invalid_one', 'invalid_2'], 'foo')

        # invalid modules and attr
        invalid = import_attr(['invalid_one', 'invalid_2'], 'foo',
                              raise_error=False)
        self.assertIsNone(invalid)

        # invalid attr
        invalid = import_attr(['invalid_one', 'math'], '_invalid_',
                              raise_error=False)
        self.assertIsNone(invalid)

        # multiple attrs
        actual = import_attr(['invalid_one', 'math'], ['sin', 'cos'])
        self.assertEqual(actual, (math.sin, math.cos))

        # one invalid attr in a list
        self.assertRaises(AttributeError, import_attr,
                          ['invalid_one', 'math'],
                          ['sin', '_invalid_', 'cos'])

        actual = import_attr(['invalid_one', 'math'],
                             ['sin', '_invalid_', 'cos'], raise_error=False)
        self.assertEqual(actual, (math.sin, None, math.cos))

    def test_import_any_attr(self):
        math = import_module('math')

        # valid module and attr
        actual = import_any_attr(['os', 'math'], 'pi')
        self.assertEqual(actual, math.pi)

        # invalid modules
        self.assertRaises(ImportError, import_any_attr,
                          ['invalid_one', 'invalid_two'], 'pi')

        self.assertIsNone(import_any_attr(['invalid_one', 'invalid_two'],
                                          'pi', raise_error=False))

        # invalid attr
        self.assertRaises(AttributeError, import_any_attr, ['os', 'math'],
                          'goats')

        self.assertIsNone(import_any_attr(['os', 'math'], 'goats',
                                          raise_error=False))

    def test_import_all_attrs(self):
        math = import_module('math')

        # valid module
        attrs = import_all_attrs(['math'])
        self.assertIn('pi', attrs)
        self.assertEqual(attrs['pi'], math.pi)

        # two valid modules
        attrs = import_all_attrs(['math', 'os'])
        self.assertIn('pi', attrs)
        self.assertEqual(attrs['pi'], math.pi)
        self.assertNotIn('environ', attrs)

        # one invalid module
        attrs = import_all_attrs(['invalid_one', 'math'])
        self.assertIn('pi', attrs)
        self.assertEqual(attrs['pi'], math.pi)

        # invalid modules
        self.assertRaises(ImportError, import_all_attrs,
                          ['invalid_one', 'invalid_two'])

        self.assertIsNone(import_all_attrs(['invalid_one', 'invalid_two'],
                                           raise_error=False))
