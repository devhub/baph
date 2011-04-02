# -*- coding: utf-8 -*-

import inspect

from baph.utils.importing import import_all_attrs, import_attr

globals().update(import_all_attrs(['django.test.client']))
Client = import_attr(['django.test.client'], 'Client')
login = import_attr(['baph.auth'], 'login')
StringIO = import_attr(['cStringIO', 'StringIO'], 'StringIO')

# monkeypatching Client to use baph.auth
exec inspect.getsource(Client)
