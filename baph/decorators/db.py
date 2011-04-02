# -*- coding: utf-8 -*-
'''\
:mod:`baph.decorators.db` -- Database-related Decorators
========================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from baph.db.orm import ORM
from functools import wraps

orm = ORM.get()


def sqlalchemy_session(f):
    '''Decorator that automatically attaches a SQLAlchemy session to a
    function.
    '''

    @wraps(f)
    def _handler(*args, **kwargs):
        if not kwargs.get('session'):
            kwargs['session'] = orm.sessionmaker()
        try:
            return f(*args, **kwargs)
        except Exception:
            kwargs['session'].rollback()
            raise

    return _handler
