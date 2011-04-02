# -*- coding: utf-8 -*-

from baph.auth import login
from coffin.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import authenticate
from facebook import get_user_from_cookie


def facebook_login(request):
    if hasattr(request, 'orm'):
        session = request.orm.sessionmaker()
    else:
        from baph.db.orm import ORM
        session = ORM.get().sessionmaker()
    params = get_user_from_cookie(request.COOKIES, settings.FACEBOOK_APP_ID,
                                  settings.FACEBOOK_SECRET_KEY)
    if params:
        user = authenticate(uid=params['uid'], session=session)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(settings.LOGIN_REDIRECT_URL, {}, ())
            else:
                # Disabled account, redirect and notify?
                return redirect('/', {}, ())
        else:
            # Invalid user, redirect and notify?
            return redirect('/', {}, ())
    elif request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL, {}, ())
    else:
        return redirect('/account/register/', {}, ())
