# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required

from coffin.shortcuts import render_to_response
from coffin.template import RequestContext
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlencode
from piston.authentication.oauth.forms import AuthorizeRequestTokenForm
from piston.authentication.oauth.store import store, InvalidTokenError

from piston.authentication.oauth.utils import get_oauth_request
from piston.authentication.oauth.views import (
    get_request_token, get_access_token)

__all__ = ['get_request_token', 'authorize_request_token', 'get_access_token']
DEFAULT_VERIFY_TPL = 'piston/oauth/authorize_verification_code.html'

# can't monkeypatch because of the decorator


@login_required
def authorize_request_token(request, form_class=AuthorizeRequestTokenForm,
                            template_name='piston/oauth/authorize.html',
                            verification_template_name=DEFAULT_VERIFY_TPL):
    if 'oauth_token' not in request.REQUEST:
        return HttpResponseBadRequest('No request token specified.')

    oauth_request = get_oauth_request(request)

    try:
        request_token = store.get_request_token(request, oauth_request,
                                                request.REQUEST['oauth_token'])
    except InvalidTokenError:
        return HttpResponseBadRequest('Invalid request token.')

    consumer = store.get_consumer_for_request_token(request, oauth_request,
                                                    request_token)

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid() and form.cleaned_data['authorize_access']:
            request_token = store.authorize_request_token(request,
                                                          oauth_request,
                                                          request_token)
            if request_token.callback is not None and \
               request_token.callback != 'oob':
                url = '%s&%s' % (request_token.get_callback_url(),
                                 urlencode({
                    'oauth_token': request_token.key,
                }))
                return HttpResponseRedirect(url)
            else:
                return render_to_response(verification_template_name, {
                    'consumer': consumer,
                    'verification_code': request_token.verifier,
                }, RequestContext(request))
    else:
        form = form_class(initial={
            'oauth_token': request_token.key,
        })

    return render_to_response(template_name, {
        'consumer': consumer,
        'form': form,
    }, RequestContext(request))
