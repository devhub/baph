# -*- coding: utf-8 -*-

from baph.auth.models import User
from baph.decorators.db import sqlalchemy_session
from .models import FacebookProfile


class FacebookBackend:

    @sqlalchemy_session
    def authenticate(self, uid=None, session=None):
        profile = session.query(FacebookProfile) \
                         .filter_by(uid=uid) \
                         .first()
        if profile:
            return profile.user
        else:
            return None

    @sqlalchemy_session
    def get_user(self, user_id=None, session=None):
        return session.query(User).get(user_id)
