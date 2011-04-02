# -*- coding: utf-8 -*-

from baph.auth import login as auth_login
from baph.auth.registration.views import register
from coffin.shortcuts import redirect, render_to_response
from coffin.template import RequestContext
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect
from .forms import TwitterRegistrationForm
from .. import SESSION_KEY, Twitter

BACKEND = 'baph.socialmedia.twitter.auth.TwitterBackend'


def twitter_registration(request):
    twitter = Twitter()
    view = 'twitter_register_complete'
    auth_url = twitter.set_request_token(request, view,
                                         signin_with_twitter=True)
    context = {
        'twitter_auth_url': auth_url,
    }
    return register(request, BACKEND, extra_context=context,
                    template_name='twitter/auth/register.html')


def complete_registration(request):
    if request.method == 'POST':
        return register(request, BACKEND)
    form = None
    if 'denied' in request.GET:
        template_name = 'twitter/auth/denied.html'
    elif 'oauth_token' in request.GET and 'oauth_verifier' in request.GET:
        form = TwitterRegistrationForm(initial={
            'oauth_token': request.GET['oauth_token'],
            'oauth_verifier': request.GET['oauth_verifier'],
        })
        template_name = 'twitter/auth/complete.html'
    else:
        return redirect('/', (), {})
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))


def login(request):
    twitter = Twitter()
    view = 'twitter_login_complete'
    auth_url = twitter.set_request_token(request, view,
                                         signin_with_twitter=True)
    return HttpResponseRedirect(auth_url)


def complete_login(request):
    redirect_path = '/'
    if 'oauth_token' in request.GET and 'oauth_verifier' in request.GET:
        token = request.GET['oauth_token']
        verifier = request.GET['oauth_verifier']
        request_token = request.session.pop(SESSION_KEY, None)
        if request_token and request_token.key == token:
            twitter = Twitter(request_token)
            access_token = twitter.get_access_token(verifier)
            if access_token:
                if hasattr(request, 'orm'):
                    session = request.orm.sessionmaker()
                else:
                    session = None
                user = authenticate(oauth_token=access_token.key,
                                    uid=twitter.user.id, session=session)
                auth_login(request, user)
                redirect_path = settings.LOGIN_REDIRECT_URL
    return redirect(redirect_path, (), {})
