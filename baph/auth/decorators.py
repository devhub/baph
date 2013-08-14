# -*- coding: utf-8 -*-
import logging
import time

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


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
        logging.debug('%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper
