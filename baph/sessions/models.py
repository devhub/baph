# -*- coding: utf-8 -*-
'''\
:mod:`baph.sessions.models` -- SQLAlchemy models for Django sessions
====================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from baph.db.orm import ORM
from baph.db.models import Model
from sqlalchemy import Column, DateTime, String, Text

orm = ORM.get()


class Session(orm.Base, Model):
    '''The model for the Django session database backend.'''
    __tablename__ = 'django_session'

    session_key = Column(String(40), nullable=False, primary_key=True)
    # XXX Django makes this LONGTEXT in MySQL?
    session_data = Column(Text, nullable=False)
    expire_date = Column(DateTime, nullable=False)
