# -*- coding: utf-8 -*-
'''Views which allow users to create and activate accounts.'''

from baph.utils.importing import import_attr
import inspect
(activate, register) = \
    import_attr(['registration.views'], ['activate', 'register'])

# replace the Django imports, per
# http://www.davidcramer.net/code/486/jinja2-and-django-registration.html
(redirect, render_to_response) = \
    import_attr(['coffin.shortcuts'], ['redirect', 'render_to_response'])
RequestContext = import_attr(['coffin.template'], 'RequestContext')
get_backend = import_attr(['registration.backends'], 'get_backend')

exec inspect.getsource(activate)
exec inspect.getsource(register)
