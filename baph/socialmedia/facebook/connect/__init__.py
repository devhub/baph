# -*- coding: utf-8 -*-
'''\
:mod:`baph.socialmedia.facebook.connect` -- Registration via Facebook Connect
=============================================================================

Based on http://github.com/policus/django-registration-facebook-backend
'''

from baph.auth import login
from baph.auth.models import AnonymousUser, User
from baph.auth.registration import signals
from baph.socialmedia.facebook import Facebook
from django.contrib.auth import authenticate
from django.forms import Form
from django.conf import settings
from facebook import get_user_from_cookie
from .models import FacebookProfile


class FacebookConnectBackend(object):

    def register(self, request, **kwargs):
        if hasattr(request, 'orm'):
            session = request.orm.sessionmaker()
        else:
            from baph.db.orm import ORM
            session = ORM.get().sessionmaker()
        params = get_user_from_cookie(request.COOKIES,
                                      settings.FACEBOOK_APP_ID,
                                      settings.FACEBOOK_SECRET_KEY)
        if params and 'uid' in params:
            uid = params['uid']
            profile = session.query(FacebookProfile) \
                             .filter_by(uid=uid) \
                             .first()
            if profile:
                user_obj = profile.user
            else:
                # Check that the username is unique, and if so, create a user
                # and profile
                username = 'fb:%s' % uid
                user_ct = session.query(User) \
                                 .filter_by(username=username) \
                                 .count()
                if user_ct == 0:
                    fb = Facebook(params['access_token'])
                    fb_user = fb.user
                    user_obj = User.create_user(username=username,
                                                email=fb_user['email'],
                                                password=None,
                                                session=session)
                    user_obj.first_name = fb_user['first_name']
                    user_obj.last_name = fb_user['last_name']
                    profile = FacebookProfile(
                        user=user_obj,
                        uid=uid,
                        access_token=params['access_token'],
                        expires_in=params['expires'],
                    )
                    session.add(profile)
                    session.commit()
                else:
                    # Should we redirect here, or return False and redirect in
                    # post_registration_redirect?
                    return False

            signals.user_registered.send(sender=self.__class__, user=user_obj,
                                         request=request)

            user = authenticate(uid=uid, session=session)
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
        # Pass back an empty instance of the form class, because we are not
        # using a registration form.
        return Form

    def post_registration_redirect(self, request, user):
        if user is False:
            redirect_url = '/'
        else:
            redirect_url = getattr(settings,
                                   'FACEBOOK_POST_REGISTRATION_REDIRECT',
                                   settings.LOGIN_REDIRECT_URL)
        return (redirect_url, (), {})

    def activate(self, request):
        return NotImplementedError

    def post_activation_redirect(self, request, user):
        return NotImplementedError
