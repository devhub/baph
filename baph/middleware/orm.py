# -*- coding: utf-8 -*-
'''\
:mod:`baph.middleware.orm` -- SQLAlchemy ORM Middleware
=======================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from baph.db.orm import ORM


class SQLAlchemyMiddleware(object):
    '''Django middleware which adds an ORM instance to the request object.
    If the request throws an exception, the current SQL transaction is rolled
    back.
    '''

    def process_request(self, request):
        request.orm = ORM.get()

    def process_response(self, request, response):
        if hasattr(request, 'orm'):
            request.orm.sessionmaker.remove()
            request.orm.sessionmaker.close()
        return response

    def process_exception(self, request, exception):
        if hasattr(request, 'orm'):
            request.orm.sessionmaker.rollback()
            request.orm.sessionmaker.remove()
            request.orm.sessionmaker.close()
        return None
