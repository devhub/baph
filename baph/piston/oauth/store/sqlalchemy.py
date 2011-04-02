# -*- coding: utf-8 -*-

from baph.decorators.db import sqlalchemy_session
from baph.piston.models import Nonce, Token, Consumer, VERIFIER_SIZE
from datetime import datetime
import oauth2 as oauth
from piston.authentication.oauth.store import (
    InvalidConsumerError, InvalidTokenError, Store)


class ModelStore(Store):
    '''Store implementation using the SQLAlchemy models defined in
    :mod:`baph.piston.models`.
    '''

    @sqlalchemy_session
    def get_object_or_exception(self, cls, exception, session=None, **kwargs):
        kwargs.pop('request', None)
        obj = session.query(cls) \
                     .filter_by(**kwargs) \
                     .first()
        if obj:
            return obj
        else:
            raise exception()

    def get_consumer(self, request, oauth_request, consumer_key):
        return self.get_object_or_exception(Consumer, InvalidConsumerError,
                                            request=request, key=consumer_key)

    def get_consumer_for_request_token(self, request, oauth_request,
                                       request_token):
        return request_token.consumer

    def get_consumer_for_access_token(self, request, oauth_request,
                                      access_token):
        return access_token.consumer

    @sqlalchemy_session
    def create_request_token(self, request, oauth_request, consumer, callback,
                             session=None):
        consumer = session.query(Consumer) \
                          .filter_by(key=oauth_request['oauth_consumer_key']) \
                          .first()
        oauth_ts = float(oauth_request['oauth_timestamp'])
        timestamp = datetime.fromtimestamp(oauth_ts)
        token = Token.create(token_type=Token.REQUEST, consumer=consumer,
                             timestamp=timestamp, _commit=False,
                             session=session)
        token.set_callback(callback, session=session)

        return token

    def get_request_token(self, request, oauth_request, request_token_key):
        return self.get_object_or_exception(Token, InvalidTokenError,
                                            request=request,
                                            key=request_token_key,
                                            token_type=Token.REQUEST)

    @sqlalchemy_session
    def authorize_request_token(self, request, oauth_request, request_token,
                                session=None):
        request_token.is_approved = True
        request_token.user = request.user
        request_token.verifier = oauth.generate_verifier(VERIFIER_SIZE)
        session.commit()

        return request_token

    @sqlalchemy_session
    def create_access_token(self, request, oauth_request, consumer,
                            request_token, session=None):
        sconsumer = session.query(Consumer) \
                           .filter_by(key=consumer.key) \
                           .first()
        oauth_ts = float(oauth_request['oauth_timestamp'])
        timestamp = datetime.fromtimestamp(oauth_ts)
        access_token = Token.create(token_type=Token.ACCESS,
                                    timestamp=timestamp, consumer=sconsumer,
                                    user=request_token.user, session=session,
                                    _commit=False)
        session.delete(request_token)
        session.commit()

        return access_token

    def get_access_token(self, request, oauth_request, consumer,
                         access_token_key):
        return self.get_object_or_exception(Token, InvalidTokenError,
                                            request=request,
                                            key=access_token_key,
                                            token_type=Token.ACCESS)

    def get_user_for_access_token(self, request, oauth_request, access_token):
        return access_token.user

    def get_user_for_consumer(self, request, oauth_request, consumer):
        return consumer.user

    @sqlalchemy_session
    def check_nonce(self, request, oauth_request, nonce, session=None):
        consumer_key = oauth_request['oauth_consumer_key']
        token_key = oauth_request.get('oauth_token', '')
        nonce_obj = session.query(Nonce) \
                           .filter_by(consumer_key=consumer_key,
                                      token_key=token_key,
                                      key=nonce) \
                           .first()
        created = not nonce_obj
        if created:
            nonce_obj = Nonce(consumer_key=consumer_key,
                              token_key=token_key, key=nonce)
            session.add(nonce_obj)
            session.commit()
        return created
