# -*- coding: utf-8 -*-
from __future__ import absolute_import
import decorator
import logging
import time

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from six.moves import zip


def check_perm(resource, action, simple=True, extra_keys={}, filters={}):
    ''' checks user permissions to determine whether to allow user access
    :resource: [string] corresponds to 'resource' value in db, ex: 'site'
    :action: [string] corresponds to 'action' value in db, ex 'view'
    :simple: [bool] True = checks if any permission exists for the 
    :   resource.action pair. False = apply base filters, extra_keys,
    :   and filters to a model to determine more granular permissions
    :extra_keys: [dict] each key is a param to extract from kwargs and each
    :   value is the corresponding db field, ex {'site_hash','hash'}
    :filters: [dict] key/value pairs of filter conditions to apply to
    :   the model query, ex {'deleted':0}
    '''
    def check_perm_closure(f, request, *args, **kwargs):

        if not kwargs:
            keys = f.__code__.co_varnames[1:] #item 0 is 'request'
            kwargs = dict(list(zip(keys,args)))
            args = []

        for url_key, db_key in extra_keys.items():
            filters[db_key] = kwargs[url_key]

        if request.user.has_perm(resource, action, filters):
            return f(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')

    return decorator.decorator(check_perm_closure)

def superuser_required(function=None,
                       redirect_field_name=REDIRECT_FIELD_NAME):
    '''Decorator for views that checks that the user is a superuser,
    redirecting to the log-in page if necessary. Derived from
    django.contrib.auth.decorators.login_required.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator

def staff_required(function=None,
                   redirect_field_name=REDIRECT_FIELD_NAME):
    '''Decorator for views that checks that the user is a staff member,
    redirecting to the log-in page if necessary. Derived from
    django.contrib.auth.decorators.login_required.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_staff,
        redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        logging.debug('%s took %0.3f ms' % (func.__name__, (t2-t1)*1000.0))
        return res
    return wrapper
