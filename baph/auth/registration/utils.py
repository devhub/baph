from baph.auth.registration import settings


def signin_redirect(redirect=None, user=None):
    """
    -ported from userena
    Redirect user after successful sign in.

    First looks for a ``requested_redirect``. If not supplied will fall-back to
    the user specific account page. If all fails, will fall-back to the standard
    Django ``LOGIN_REDIRECT_URL`` setting. Returns a string defining the URI to
    go next.

    :param redirect:
        A value normally supplied by ``next`` form field. Gets preference
        before the default view which requires the user.

    :param user:
        A ``User`` object specifying the user who has just signed in.

    :return: String containing the URI to redirect to.

    """
    if redirect: return redirect
    elif user is not None:
        return settings.BAPH_SIGNIN_REDIRECT_URL % \
                {'username': user.username}
    else: return settings.LOGIN_REDIRECT_URL

def get_protocol():
    """
    Returns a string with the current protocol.

    This can be either 'http' or 'https' depending on ``BAPH_USE_HTTPS``
    setting.

    """
    protocol = 'http'
    if settings.BAPH_USE_HTTPS:
        protocol = 'https'
    return protocol
