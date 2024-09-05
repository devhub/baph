# -*- coding: utf-8 -*-
'''\
:mod:`baph.middleware.orm` -- SQLAlchemy ORM Middleware
=======================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from baph.db.orm import ORM


class SQLAlchemyMiddleware(object):
    ''' Django middleware which closes the request-bound session
        If the request throws an exception, the current SQL transaction 
        is rolled back.
    '''
    def process_response(self, request, response):
        session = ORM.get().sessionmaker()
        if response.status_code >= 400:
            session.expunge_all()
        session.flush()
        session.close()
        return response

    def process_exception(self, request, exception):
        session = ORM.get().sessionmaker()
        session.rollback()
        return None
