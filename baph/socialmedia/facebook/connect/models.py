# -*- coding: utf-8 -*-

from baph.db.models import Model
from baph.db.orm import ORM
from baph.auth.models import User, AUTH_USER_FIELD
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relation

orm = ORM.get()


class FacebookProfile(orm.Base, Model):
    '''Facebook Connect-related information for a user.'''
    __tablename__ = 'auth_facebook_profile'

    user_id = Column(AUTH_USER_FIELD, ForeignKey(User.id), primary_key=True)
    uid = Column(String(255), nullable=False, unique=True)
    access_token = Column(String(100), nullable=True)
    expires_in = Column(Integer, default=0, nullable=False)

    user = relation(User, lazy=False)
