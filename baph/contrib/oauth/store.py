from __future__ import absolute_import
from datetime import datetime

from django.conf import settings
from oauth_provider.store import InvalidConsumerError, InvalidTokenError, Store
from sqlalchemy import or_

from baph.auth.models import User, Organization, OAuthConsumer, OAuthNonce
from baph.db.orm import ORM


NONCE_VALID_PERIOD = getattr(settings, "OAUTH_NONCE_VALID_PERIOD", None)

orm = ORM.get()

class ModelStore(Store):
    """
    Store implementation using sqla models
    """
    def get_consumer(self, request, oauth_request, consumer_key):
        org_id = Organization.get_current_id(request)
        col_key = Organization.get_column_key()
        col = getattr(User, col_key)

        session = orm.sessionmaker()
        consumer = session.query(OAuthConsumer) \
            .join(OAuthConsumer.user) \
            .filter(OAuthConsumer.key==oauth_request['oauth_consumer_key']) \
            .filter(or_(
                col==org_id,
                User.is_superuser==True,
                )) \
            .first()
        if not consumer:
            raise InvalidConsumerError()
        return consumer

    def check_nonce(self, request, oauth_request, nonce, timestamp=0):
        """
        Return `True` if the nonce has not yet been used, `False` otherwise.

        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `nonce`: The nonce to check.
        `timestamp`: nonce timestamp.
        """
        timestamp = int(timestamp)

        if NONCE_VALID_PERIOD and int(now().strftime("%s")) \
                - timestamp > NONCE_VALID_PERIOD:
            return False

        timestamp = datetime.fromtimestamp(timestamp) \
                            .strftime('%Y-%m-%d %H:%M:%S')

        session = orm.sessionmaker()
        params = {
            'consumer_key': oauth_request['oauth_consumer_key'],
            'key': oauth_request['oauth_nonce'],
            'timestamp': timestamp,
            }
        nonce = session.query(OAuthNonce).filter_by(**params).first()
        if nonce:
            return False

        nonce = OAuthNonce(**params)
        session.add(nonce)
        session.commit()
        return True