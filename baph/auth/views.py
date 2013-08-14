# -*- coding: utf-8 -*-

import inspect

from baph.db.shortcuts import get_object_or_404
from baph.utils.importing import import_attr
render_to_response = import_attr(['coffin.shortcuts'], 'render_to_response')
from coffin.template import RequestContext
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    password_reset_complete, password_reset_done)
from django.core.urlresolvers import reverse

from django.http import Http404, HttpResponseRedirect
from django.utils.http import base36_to_int
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import re
from uuid import UUID
# avoid shadowing
from . import login as auth_login, logout as auth_logout
from .forms import PasswordResetForm, SetPasswordForm
from .models import User

# fun with monkeypatching
exec inspect.getsource(password_reset_done)
exec inspect.getsource(password_reset_complete)


@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    '''Displays the login form and handles the login action.'''

    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            # Light security check -- make sure redirect_to isn't garbage.
            if not redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Heavier security check -- redirects to http://example.com should
            # not be allowed, but things like /view/?param=http://example.com
            # should be allowed. This regex checks if there is a '//' *before*
            # a question mark.
            elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
                    redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)

    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    return render_to_response(template_name, {
        'form': form,
        redirect_field_name: redirect_to,
    }, context_instance=RequestContext(request))


def logout(request, next_page=None,
           template_name='registration/logged_out.html',
           redirect_field_name=REDIRECT_FIELD_NAME):
    '''Logs out the user and displays 'You are logged out' message.'''
    auth_logout(request)
    if next_page is None:
        redirect_to = request.REQUEST.get(redirect_field_name, '')
        if redirect_to:
            return HttpResponseRedirect(redirect_to)
        else:
            return render_to_response(template_name, {
                'title': _('Logged out'),
            }, context_instance=RequestContext(request))
    else:
        # Redirect to this page until the session has been cleared.
        return HttpResponseRedirect(next_page or request.path)


@csrf_protect
def password_reset(request, is_admin_site=False,
                   template_name='registration/password_reset_form.html',
                   email_template_name=None,
                   password_reset_form=PasswordResetForm,
                   token_generator=default_token_generator,
                   post_reset_redirect=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('baph.auth.views.password_reset_done')
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            if not email_template_name:
                email_template_name = 'registration/password_reset_email.html'
            opts = {}
            opts['use_https'] = request.is_secure()
            opts['token_generator'] = token_generator
            opts['email_template_name'] = email_template_name
            opts['request'] = request
            if is_admin_site:
                opts['domain_override'] = request.META['HTTP_HOST']
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)
    else:
        form = password_reset_form()
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))


def password_reset_confirm(request, uidb36=None, token=None,
                           template_name=None,
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None):
    '''View that checks the hash in a password reset link and presents a form
    for entering a new password. Doesn't need ``csrf_protect`` since no-one can
    guess the URL.
    '''
    assert uidb36 is not None and token is not None  # checked by URLconf
    if not template_name:
        template_name = 'registration/password_reset_confirm.html'
    if post_reset_redirect is None:
        post_reset_redirect = reverse('baph.auth.views.password_reset_complete')
    try:
        uid = UUID(int=base36_to_int(uidb36))
    except ValueError:
        raise Http404

    user = get_object_or_404(User, id=uid)
    context_instance = RequestContext(request)

    if token_generator.check_token(user, token):
        context_instance['validlink'] = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(None)
    else:
        context_instance['validlink'] = False
        form = None
    context_instance['form'] = form
    return render_to_response(template_name, context_instance=context_instance)
