# -*- coding: utf-8 -*-

from baph.db.models import Model
from baph.db.orm import ORM
from baph.auth.models import User, AUTH_USER_FIELD
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relation

orm = ORM.get()


class TwitterProfile(orm.Base, Model):
    '''Twitter-related information for a user.'''
    __tablename__ = 'auth_twitter_profile'

    user_id = Column(AUTH_USER_FIELD, ForeignKey(User.id), primary_key=True)
    uid = Column(String(255), nullable=False, unique=True)
    username = Column(String(20), nullable=False)  # Twitter username
    key = Column('token_key', String(255), nullable=False)
    secret = Column('token_secret', String(255), nullable=False)
    added = Column(DateTime, default=datetime.now, nullable=False)

    user = relation(User, lazy=False)

    def __init__(self, *args, **kwargs):
        token = kwargs.pop('access_token', None)
        if token:
            kwargs['key'] = token.key
            kwargs['secret'] = token.secret
        super(TwitterProfile, self).__init__(*args, **kwargs)

    @property
    def access_token(self):
        # avoid circular import
        from . import TwitterAccessToken
        return TwitterAccessToken(self.key, self.secret)
