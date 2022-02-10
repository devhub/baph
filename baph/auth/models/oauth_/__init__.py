from __future__ import absolute_import
from django.conf import settings
from oauth import oauth
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from baph.auth.models.user import User
from baph.db import ORM


orm = ORM.get()
Base = orm.Base

MAX_KEY_LEN = 255
MAX_SECRET_LEN = 255
KEY_LEN = 32
SECRET_LEN = 32
UNIQUE_KEY = getattr(settings, 'BAPH_UNIQUE_OAUTH_KEYS', True)


class OAuthConsumer(Base):
    __tablename__ = 'auth_oauth_consumer'
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    key = Column(String(MAX_KEY_LEN), unique=UNIQUE_KEY)
    secret = Column(String(MAX_SECRET_LEN))

    user = relationship(User, lazy=True, uselist=False)

    def as_consumer(self):
        '''Creates an oauth.OAuthConsumer object from the DB data.
        :rtype: oauth.OAuthConsumer
        '''
        return oauth.OAuthConsumer(self.key, self.secret)


class OAuthNonce(Base):
    __tablename__ = 'auth_oauth_nonce'
    __table_args__ = (
        UniqueConstraint('consumer_key', 'key', 'timestamp',
                         name='uix_consumer_nonce_timestamp'),
    )
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    token_key = Column(String(32))
    consumer_key = Column(String(MAX_KEY_LEN), nullable=False)
    key = Column(String(255), nullable=False)
