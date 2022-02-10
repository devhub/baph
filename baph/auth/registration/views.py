# -*- coding: utf-8 -*-
'''Views which allow users to create and activate accounts.'''
from __future__ import absolute_import
from coffin.shortcuts import render_to_response, redirect
from coffin.template import RequestContext
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.forms import Form
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.translation import ugettext as _
from sqlalchemy.orm.exc import NoResultFound

from baph.auth import login, logout
from baph.auth.forms import PasswordChangeForm
from baph.auth.models import User, Organization
from baph.auth.registration import settings
from baph.auth.registration.decorators import secure_required
from baph.auth.registration.forms import (SignupForm, AuthenticationForm,
    ChangeEmailForm, SignupFormOnlyEmail)
from baph.auth.registration.managers import SignupManager
from baph.auth.registration.models import UserRegistration
from baph.auth.registration.utils import signin_redirect
from baph.auth.views import logout as Signout
from baph.db.orm import ORM


orm = ORM.get()

@secure_required
def signup(request, signup_form=SignupForm,
            template_name='registration/signup_form.html',
            success_url=None, extra_context=None):
    if settings.BAPH_AUTH_WITHOUT_USERNAMES and (signup_form == SignupForm):
        signup_form = SignupFormOnlyEmail

    if request.method == 'POST':
        form = signup_form(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            if success_url: redirect_to = success_url
            else: redirect_to = reverse('baph_signup_complete')

            # A new signed user should logout the old one.
            if request.user.is_authenticated():
                logout(request)

            if (settings.BAPH_SIGNIN_AFTER_SIGNUP and
                not settings.BAPH_ACTIVATION_REQUIRED):
                user = authenticate(identification=user.email,
                                    check_password=False)
                login(request, user)

            return redirect(redirect_to)

    else:
        form = signup_form()

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

@secure_required
def activate(request, activation_key,
             template_name='registration/activate_fail.html',
             retry_template_name='registration/activate_retry.html',
             success_url=django_settings.LOGIN_REDIRECT_URL,
             extra_context=None):
    session = orm.sessionmaker()
    signup = session.query(UserRegistration) \
        .filter_by(activation_key=activation_key) \
        .first()
    if not signup:
        if not extra_context: extra_context = dict()
        return render_to_response(template_name, extra_context,
            context_instance=RequestContext(request))
    if (not signup.activation_key_expired() 
        or not settings.BAPH_ACTIVATION_RETRY):
        user = SignupManager.activate_user(activation_key)
        if user:
            auth_user = authenticate(identification=user.email,
                                     check_password=False)
            login(request, auth_user)
            messages.success(request, _('Your account has been activated and '
                'you have been signed in.'), fail_silently=True)
            if success_url: redirect_to = success_url % {'username': user.username }
            else: redirect_to = reverse('userena_profile_detail', 
                                        kwargs={'username': user.username})
                                        #TODO this is broken
            return redirect(redirect_to)
        else:
            if not extra_context: extra_context = dict()
            return render_to_response(template_name, extra_context,
                context_instance=RequestContext(request))
    else:
        if not extra_context: extra_context = dict()
        extra_context['activation_key'] = activation_key
        return render_to_response(retry_template_name, extra_context,
            context_instance=RequestContext(request))

@secure_required
def activate_retry(request, activation_key,
                   template_name='registration/activate_retry_success.html',
                   extra_context=None):
    """
    Reissue a new ``activation_key`` for the user with the expired
    ``activation_key``.

    If ``activation_key`` does not exists, or ``BAPH_ACTIVATION_RETRY`` is
    set to False and for any other error condition user is redirected to
    :func:`activate` for error message display.

    :param activation_key:
        String of a SHA1 string of 40 characters long. A SHA1 is always 160bit
        long, with 4 bits per character this makes it --160/4-- 40 characters
        long.

    :param template_name:
        String containing the template name that is used when new
        ``activation_key`` has been created. Defaults to
        ``userena/activate_retry_success.html``.

    :param extra_context:
        Dictionary containing variables which could be added to the template
        context. Default to an empty dictionary.

    """
    if not settings.BAPH_ACTIVATION_RETRY:
        return redirect(reverse('baph_activate', args=(activation_key,)))
    try:
        if SignupManager.check_expired_activation(activation_key):
            new_key = SignupManager.reissue_activation(activation_key)
            if new_key:
                if not extra_context: extra_context = dict()
                return render_to_response(template_name, extra_context,
                    context_instance=RequestContext(request))
            else:
                return redirect(reverse('baph_activate', args=(activation_key,)))
        else:
            return redirect(reverse('baph_activate', args=(activation_key,)))
    except NoResultFound:
        return redirect(reverse('baph_activate', args=(activation_key,)))

@secure_required
def signin(request, auth_form=AuthenticationForm,
           template_name='registration/signin_form.html',
           redirect_field_name=REDIRECT_FIELD_NAME,
           redirect_signin_function=signin_redirect, extra_context=None):
    """
    Signin using email or username with password.

    Signs a user in by combining email/username with password. If the
    combination is correct and the user :func:`is_active` the
    :func:`redirect_signin_function` is called with the arguments
    ``REDIRECT_FIELD_NAME`` and an instance of the :class:`User` who is is
    trying the login. The returned value of the function will be the URL that
    is redirected to.

    A user can also select to be remembered for ``USERENA_REMEMBER_DAYS``.

    :param auth_form:
        Form to use for signing the user in. Defaults to the
        :class:`AuthenticationForm` supplied by userena.

    :param template_name:
        String defining the name of the template to use. Defaults to
        ``userena/signin_form.html``.

    :param redirect_field_name:
        Form field name which contains the value for a redirect to the
        succeeding page. Defaults to ``next`` and is set in
        ``REDIRECT_FIELD_NAME`` setting.

    :param redirect_signin_function:
        Function which handles the redirect. This functions gets the value of
        ``REDIRECT_FIELD_NAME`` and the :class:`User` who has logged in. It
        must return a string which specifies the URI to redirect to.

    :param extra_context:
        A dictionary containing extra variables that should be passed to the
        rendered template. The ``form`` key is always the ``auth_form``.

    **Context**

    ``form``
        Form used for authentication supplied by ``auth_form``.

    """
    form = auth_form()

    if request.method == 'POST':
        form = auth_form(request.POST, request.FILES)
        if form.is_valid():
            identification, password, remember_me = (form.cleaned_data['identification'],
                                                     form.cleaned_data['password'],
                                                     form.cleaned_data['remember_me'])
            user = authenticate(identification=identification,
                                password=password)
            if user.is_active:
                login(request, user)
                if remember_me:
                    request.session.set_expiry(settings.BAPH_REMEMBER_ME_DAYS[1] * 86400)
                else: request.session.set_expiry(0)

                messages.success(request, _('You have been signed in.'),
                    fail_silently=True)

                # Whereto now?
                redirect_to = redirect_signin_function(
                    request.REQUEST.get(redirect_field_name), user)
                return HttpResponseRedirect(redirect_to)
            else:
                return redirect(reverse('baph_disabled'))

    if not extra_context: extra_context = dict()
    extra_context.update({
        'form': form,
        'next': request.REQUEST.get(redirect_field_name),
    })
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

@secure_required
def signout(request, next_page=settings.BAPH_REDIRECT_ON_SIGNOUT,
            template_name='registration/signout.html', *args, **kwargs):
    """
    (ported from userena)
    Signs out the user and adds a success message ``You have been signed
    out.`` If next_page is defined you will be redirected to the URI. If
    not the template in template_name is used.

    :param next_page:
        A string which specifies the URI to redirect to.

    :param template_name:
        String defining the name of the template to use. Defaults to
        ``userena/signout.html``.

    """
    if request.user.is_authenticated() and settings.BAPH_USE_MESSAGES: # pragma: no cover
        messages.success(request, _('You have been signed out.'), fail_silently=True)
    return Signout(request, next_page, template_name, *args, **kwargs)

def signup_complete(request, template_name='registration/signup_complete.html',
                     extra_context=None):
    if not extra_context: extra_context = dict()
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

def direct_to_template(request, template_name=None, extra_context=None):
    if not extra_context: extra_context = dict()
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

def direct_to_user_template(request, template_name=None, extra_context=None):
    if not extra_context: extra_context = dict()
    extra_context['viewed_user'] = request.user
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

@secure_required
def email_change(request, email_form=ChangeEmailForm,
                 template_name='registration/email_form.html', 
                 success_url=None, extra_context=None):
    """
    Change email address

    :param username:
        String of the username which specifies the current account.

    :param email_form:
        Form that will be used to change the email address. Defaults to
        :class:`ChangeEmailForm` supplied by userena.

    :param template_name:
        String containing the template to be used to display the email form.
        Defaults to ``userena/email_form.html``.

    :param success_url:
        Named URL where the user will get redirected to when successfully
        changing their email address.  When not supplied will redirect to
        ``userena_email_complete`` URL.

    :param extra_context:
        Dictionary containing extra variables that can be used to render the
        template. The ``form`` key is always the form supplied by the keyword
        argument ``form`` and the ``user`` key by the user whose email address
        is being changed.

    **Context**

    ``form``
        Form that is used to change the email address supplied by ``form``.

    ``account``
        Instance of the ``Account`` whose email address is about to be changed.

    **Todo**

    Need to have per-object permissions, which enables users with the correct
    permissions to alter the email address of others.

    """
    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()

    form = email_form(user)

    if request.method == 'POST':
        form = email_form(user,
                               request.POST,
                               request.FILES)

        if form.is_valid():
            email_result = form.save()

            if success_url: redirect_to = success_url
            else: redirect_to = reverse('baph_email_change_complete')
            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

@secure_required
def password_change(request, template_name='registration/password_form.html',
                    pass_form=PasswordChangeForm, success_url=None, 
                    extra_context=None):
    """ Change password of user.

    This view is almost a mirror of the view supplied in
    :func:`contrib.auth.views.password_change`, with the minor change that in
    this view we also use the username to change the password. This was needed
    to keep our URLs logical (and REST) across the entire application. And
    that in a later stadium administrators can also change the users password
    through the web application itself.

    :param username:
        String supplying the username of the user who's password is about to be
        changed.

    :param template_name:
        String of the name of the template that is used to display the password
        change form. Defaults to ``userena/password_form.html``.

    :param pass_form:
        Form used to change password. Default is the form supplied by Django
        itself named ``PasswordChangeForm``.

    :param success_url:
        Named URL that is passed onto a :func:`reverse` function with
        ``username`` of the active user. Defaults to the
        ``userena_password_complete`` URL.

    :param extra_context:
        Dictionary of extra variables that are passed on to the template. The
        ``form`` key is always used by the form supplied by ``pass_form``.

    **Context**

    ``form``
        Form used to change the password.

    """
    user = request.user

    form = pass_form(user=user)

    if request.method == "POST":
        form = pass_form(user=user, data=request.POST)
        if form.is_valid():
            form.save()

            # Send a signal that the password has changed 
            # TODO: implement signals
            #userena_signals.password_complete.send(sender=None,
            #                                       user=user)

            if success_url: redirect_to = success_url
            else: redirect_to = reverse('baph_password_change_complete')
            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    return render_to_response(template_name, extra_context,
        context_instance=RequestContext(request))

@secure_required
def email_confirm(request, confirmation_key,
                  template_name='registration/email_confirm_fail.html',
                  success_url=None, extra_context=None):
    """
    Confirms an email address with a confirmation key.

    Confirms a new email address by running :func:`User.objects.confirm_email`
    method. If the method returns an :class:`User` the user will have his new
    e-mail address set and redirected to ``success_url``. If no ``User`` is
    returned the user will be represented with a fail message from
    ``template_name``.

    :param confirmation_key:
        String with a SHA1 representing the confirmation key used to verify a
        new email address.

    :param template_name:
        String containing the template name which should be rendered when
        confirmation fails. When confirmation is successful, no template is
        needed because the user will be redirected to ``success_url``.

    :param success_url:
        String containing the URL which is redirected to after a successful
        confirmation.  Supplied argument must be able to be rendered by
        ``reverse`` function.

    :param extra_context:
        Dictionary of variables that are passed on to the template supplied by
        ``template_name``.

    """
    user = SignupManager.confirm_email(confirmation_key)
    if user:
        messages.success(request, _('Your email address has been changed.'),
                         fail_silently=True)

        if success_url: redirect_to = success_url
        else: redirect_to = reverse('baph_email_confirm_complete')
        return redirect(redirect_to)
    else:
        if not extra_context: extra_context = dict()
        return render_to_response(template_name, extra_context,
            context_instance=RequestContext(request))

