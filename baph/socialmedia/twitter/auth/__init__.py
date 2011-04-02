# -*- coding: utf-8 -*-
'''\
:mod:`baph.socialmedia.twitter.auth` -- Registration via Twitter
================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from baph.auth import login
from baph.auth.models import AnonymousUser, User
from baph.auth.registration import signals
from baph.decorators.db import sqlalchemy_session
from django.contrib.auth import authenticate
from django.conf import settings
from .. import SESSION_KEY, Twitter
from .models import TwitterProfile
from .forms import TwitterRegistrationForm


class TwitterBackend(object):
    '''Both the registration backend and the authentication backend for
    Twitter.
    '''

    def register(self, request, oauth_token, oauth_verifier, given_name,
                 family_name, email):
        if hasattr(request, 'orm'):
            session = request.orm.sessionmaker()
        else:
            from baph.db.orm import ORM
            session = ORM.get().sessionmaker()
        request_token = request.session.pop(SESSION_KEY, None)
        if request_token and request_token.key == oauth_token:
            twitter = Twitter(request_token)
            access_token = twitter.get_access_token(oauth_verifier)
            if not access_token:
                return False
            profile = session.query(TwitterProfile) \
                             .filter_by(key=access_token.key,
                                        secret=access_token.secret) \
                             .first()
            if profile:
                user_obj = profile.user
            else:
                # Check that the username is unique, and if so, create a user
                # and profile
                twitter_user = twitter.user
                username = 'twitter:%s' % twitter_user.id
                user_ct = session.query(User) \
                                 .filter_by(username=username) \
                                 .count()
                if user_ct == 0:
                    user_obj = User.create_user(username=username,
                                                email=email,
                                                password=None,
                                                session=session)
                    user_obj.first_name = given_name
                    user_obj.last_name = family_name
                    profile = TwitterProfile(user=user_obj,
                                             uid=twitter_user.id,
                                             username=twitter.username,
                                             access_token=access_token)
                    session.add(profile)
                    session.commit()
                else:
                    # Should we redirect here, or return False and redirect in
                    # post_registration_redirect?
                    return False

            signals.user_registered.send(sender=self.__class__, user=user_obj,
                                         request=request)

            user = authenticate(oauth_token=access_token.key,
                                uid=twitter_user.id, session=session)
            login(request, user)
        elif request.user.is_authenticated():
            user_obj = request.user
        else:
            # Perhaps we should handle this differently?
            user_obj = AnonymousUser()
        return user_obj

    def registration_allowed(self, request):
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_form_class(self, request):
        return TwitterRegistrationForm

    def post_registration_redirect(self, request, user):
        if user is False:
            redirect_url = '/'
        else:
            redirect_url = getattr(settings,
                                   'TWITTER_POST_REGISTRATION_REDIRECT',
                                   settings.LOGIN_REDIRECT_URL)
        return (redirect_url, (), {})

    def activate(self, request):
        return NotImplementedError

    def post_activation_redirect(self, request, user):
        return NotImplementedError

    @sqlalchemy_session
    def authenticate(self, uid=None, oauth_token=None, session=None):
        profile = session.query(TwitterProfile) \
                         .filter_by(uid=uid, key=oauth_token) \
                         .first()
        if profile:
            return profile.user
        else:
            return None

    @sqlalchemy_session
    def get_user(self, user_id=None, session=None):
        return session.query(User).get(user_id)
