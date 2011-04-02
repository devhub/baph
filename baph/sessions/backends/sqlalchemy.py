# -*- coding: utf-8 -*-
'''\
:mod:`baph.sessions.backends.sqlalchemy` -- SQLAlchemy Session Backend
======================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from __future__ import absolute_import

from datetime import datetime
from django.contrib.sessions.backends.base import CreateError, SessionBase
from django.utils.encoding import force_unicode
from sqlalchemy.exc import SQLAlchemyError
from ..models import orm, Session


class SessionStore(SessionBase):
    '''Implements an SQLAlchemy-based session store for Django.

    To use, set ``SESSION_ENGINE`` in ``settings.py`` to
    ``baph.sessions.backends.sqlalchemy``.
    '''

    def load(self):
        sess = orm.sessionmaker()
        dsession = sess.query(Session) \
                   .filter_by(session_key=self.session_key) \
                   .filter(Session.expire_date > datetime.now()) \
                   .first()
        if dsession is None:
            self.create()
            return {}
        else:
            return self.decode(force_unicode(dsession.session_data))

    def exists(self, session_key):
        sess = orm.sessionmaker()
        return sess.query(Session) \
               .filter_by(session_key=session_key) \
               .count() > 0

    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
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
        sess = orm.sessionmaker()
        if self.exists(self.session_key) and must_create:
            raise CreateError
        sess.begin(subtransactions=True)
        try:
            session_data = self.encode(self._get_session(no_load=must_create))
            obj = Session(session_key=self.session_key,
                          session_data=session_data,
                          expire_date=self.get_expiry_date())
            sess.merge(obj)
            sess.commit()
        except SQLAlchemyError:
            sess.rollback()
            raise

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            else:
                session_key = self._session_key
        sess = orm.sessionmaker()
        sess.query(Session) \
            .filter_by(session_key=session_key) \
            .delete()
