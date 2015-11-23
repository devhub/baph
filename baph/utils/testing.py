import inspect
import unittest


NO_DEFAULT = object()
AUTO_VALUE = object()
REQUIRED = object()

def is_fieldset(value):
    if inspect.isclass(value) and issubclass(value, FieldsetValidator):
        return True
    return False

class FieldsetValidator(object):
    clearable = []
    testcase = unittest.FunctionTestCase(None)

    @classmethod
    def get_base_data(cls):
        ''' return the minimal keys in a returned object '''
        return dict((key, default) for key, (base, default)
            in cls.fields.items() if base)

    @classmethod
    def validate(cls, data):
        ''' validate any object, regardless of field count '''
        base_data = cls.get_base_data()
        base_keys = set(base_data.keys()) - set(cls.clearable)
        all_keys = set(cls.fields.keys())
        data_keys = set(data.keys())
        extra_keys = data_keys - base_keys
        cls.testcase.assertItemsEqual(data_keys & base_keys, base_keys)
        cls.testcase.assertItemsEqual(all_keys & extra_keys, extra_keys)
        for k in data_keys:
            base, default = cls.fields[k]
            if is_fieldset(default):
                default.validate(data[k])

    @classmethod
    def validate_minimal(cls, data):
        ''' validate an object created with minimal fields '''
        base_data = cls.get_base_data()
        base_keys = set(base_data.keys())
        all_keys = set(cls.fields.keys())
        data_keys = set(data.keys())
        cls.testcase.assertItemsEqual(data_keys, base_keys)
        for k in base_keys:
            base, default = cls.fields[k]
            if is_fieldset(default):
                default.validate_minimal(data[k])
            elif default in (NO_DEFAULT, AUTO_VALUE, REQUIRED):
                continue
            else:
                cls.testcase.assertEqual(data[k], default)

    @classmethod
    def validate_full(cls, data):
        ''' validate an object created with maximum fields '''
        base_data = cls.get_base_data()
        base_keys = set(base_data.keys())
        all_keys = set(cls.fields.keys())
        data_keys = set(data.keys())
        cls.testcase.assertItemsEqual(data_keys, all_keys)
        for k in all_keys:
            base, default = cls.fields[k]
            if is_fieldset(default):
                default.validate_full(data[k])
