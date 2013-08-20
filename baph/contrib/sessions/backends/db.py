# -*- coding: utf-8 -*-
'''\
:mod:`baph.sessions.backends.sqlalchemy` -- SQLAlchemy Session Backend
======================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from __future__ import absolute_import

from datetime import datetime
from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.utils.encoding import force_unicode
from sqlalchemy.exc import SQLAlchemyError

from baph.db.orm import ORM


orm = ORM.get()

class SessionStore(SessionBase):
    '''Implements an SQLAlchemy-based session store for Django.

    To use, set ``SESSION_ENGINE`` in ``settings.py`` to
    ``baph.contrib.sessions.backends.sqlalchemy``.
    '''

    def load(self):
        session = orm.sessionmaker()
        s = session.query(Session) \
                   .filter_by(session_key=self.session_key) \
                   .filter(Session.expire_date > datetime.now()) \
                   .first()
        if s is None:
            self.create()
            return {}
        else:
            return self.decode(s.session_data)

    def exists(self, session_key):
        session = orm.sessionmaker()
        return session.query(Session) \
               .filter_by(session_key=session_key) \
               .count() > 0

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                # Save immediately to ensure we have a unique entry in the
                # database.
                self.save(must_create=True)
            except CreateError:
                # Key wasn't unique. Try again.
                continue
            self.modified = True
            self._session_cache = {}
            return

    def save(self, must_create=False):
        '''Saves the current session data to the database. If 'must_create' is
        True, a database error will be raised if the saving operation doesn't
        create a *new* entry (as opposed to possibly updating an existing
        entry).
        '''
        obj = Session(
            session_key=self._get_or_create_session_key(),
            session_data=self.encode(self._get_session(no_load=must_create)),
            expire_date=self.get_expiry_date()
        )
        if self.exists(self.session_key) and must_create:
            raise CreateError
        session = orm.sessionmaker()
        try:
            session.merge(obj)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        session = orm.sessionmaker()
        session.query(Session) \
            .filter_by(session_key=session_key) \
            .delete()

from baph.contrib.sessions.models import Session
