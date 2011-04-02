# -*- coding: utf-8 -*-

from baph.auth.models import User
from baph.db.models import Model
from baph.db.orm import ORM
from baph.db.types import UUID
from baph.decorators.db import sqlalchemy_session
from baph.utils.importing import import_attr
from datetime import datetime
(CONSUMER_STATES, generate_random, KEY_SIZE, SECRET_SIZE, DjangoUser,
 VERIFIER_SIZE) = \
    import_attr(['piston.models'],
                ['CONSUMER_STATES', 'generate_random', 'KEY_SIZE',
                 'SECRET_SIZE', 'User', 'VERIFIER_SIZE'])
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Unicode,
    UnicodeText)
from sqlalchemy.orm import relation, validates
import urllib
import urlparse
import uuid

orm = ORM.get()


class Nonce(orm.Base, Model):
    '''Nonces for OAuth.'''
    __tablename__ = 'oauth_nonces'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    token_key = Column(String(KEY_SIZE), nullable=False)
    consumer_key = Column(String(KEY_SIZE), nullable=False)
    key = Column(String(255), nullable=False)

    def __unicode__(self):
        return u'Nonce %s for %s' % (self.key, self.consumer_key)


class KeySecretMixin(object):
    '''A mixin for a model that has a key and a secret.'''

    @sqlalchemy_session
    def generate_random_codes(self, commit=True, session=None):
        '''Used to generate random key/secret pairings. Use this after you've
        added the other data in place of commit()ting yourself.
        '''
        key = generate_random(length=KEY_SIZE)
        secret = generate_random(SECRET_SIZE)

        query = lambda s: session.query(self.__class__) \
                                 .filter_by(key=key, secret=s)

        session.autoflush = False
        while query(secret).count():
            secret = generate_random(SECRET_SIZE)
        session.autoflush = True

        self.key = key
        self.secret = secret
        if commit:
            session.commit()

    @classmethod
    @sqlalchemy_session
    def create(cls, *args, **kwargs):
        session = kwargs.pop('session', None)
        commit = kwargs.pop('_commit', True)
        obj = cls(*args, **kwargs)
        if session:
            session.add(obj)
        obj.generate_random_codes(session=session, commit=commit)
        return obj


class Consumer(orm.Base, Model, KeySecretMixin):
    '''Consumer key/secret pairs for OAuth.'''
    __tablename__ = 'oauth_consumers'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText, nullable=False)

    key = Column(String(KEY_SIZE), nullable=False)
    secret = Column(String(SECRET_SIZE), nullable=False)

    status = Column(String(15), default='pending')
    user_id = Column(UUID, ForeignKey(User.id))

    user = relation(User, backref='consumers', lazy=True, uselist=False)

    def __unicode__(self):
        return u'Consumer %s with key %s' % (self.name, self.key)

    @validates('status')
    def validate_status(self, key, status):
        assert status in [x[0] for x in CONSUMER_STATES]
        return status


class Token(orm.Base, Model, KeySecretMixin):
    '''Tokens (both request and access) for OAuth.'''
    __tablename__ = 'oauth_tokens'

    REQUEST = 1
    ACCESS = 2
    TOKEN_TYPES = {
        REQUEST: u'Request',
        ACCESS: u'Access',
    }

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    key = Column(String(KEY_SIZE), nullable=False)
    secret = Column(String(SECRET_SIZE), nullable=False)
    verifier = Column(String(VERIFIER_SIZE), nullable=True)
    token_type = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    is_approved = Column(Boolean, default=False, nullable=False)

    user_id = Column(UUID, ForeignKey(User.id))
    consumer_id = Column(UUID, ForeignKey(Consumer.id), nullable=False)

    user = relation(User, backref='tokens', lazy=True, uselist=False)
    consumer = relation(Consumer, lazy=True)

    callback = Column(String(255), nullable=True)
    callback_confirmed = Column(Boolean, default=False, nullable=False)

    def __unicode__(self):
        return u'%s Token %s for %s' % (self.get_token_type_display(),
                                        self.key, self.consumer)

    @validates('token_type')
    def validate_token_type(self, key, token_type):
        assert token_type in self.TOKEN_TYPES
        return token_type

    def get_token_type_display(self):
        return self.TOKEN_TYPES.get(self.token_type, u'Unknown')

    def to_string(self, only_key=False):
        token_dict = {
            'oauth_token': self.key,
            'oauth_token_secret': self.secret,
            'oauth_callback_confirmed': 'true',
        }

        if self.verifier:
            token_dict.update({ 'oauth_verifier': self.verifier })

        if only_key:
            del token_dict['oauth_token_secret']

        return urllib.urlencode(token_dict)

    # -- OAuth 1.0a stuff

    def get_callback_url(self):
        if self.callback and self.verifier:
            # Append the oauth_verifier.
            parts = urlparse.urlparse(self.callback)
            scheme, netloc, path, params, query, fragment = parts[:6]
            if query:
                query = '%s&oauth_verifier=%s' % (query, self.verifier)
            else:
                query = 'oauth_verifier=%s' % self.verifier
            return urlparse.urlunparse((scheme, netloc, path, params,
                query, fragment))
        return self.callback

    @sqlalchemy_session
    def set_callback(self, callback, commit=True, session=None):
        if callback != 'oob':  # out of band, says "we can't do this!"
            self.callback = callback
            self.callback_confirmed = True
        if commit:
            session.commit()
