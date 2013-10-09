from django.conf import settings


gettext = lambda s: s

BAPH_SIGNIN_AFTER_SIGNUP = getattr(settings,
                                    'BAPH_SIGNIN_AFTER_SIGNUP',
                                    False)

BAPH_REDIRECT_ON_SIGNOUT = getattr(settings,
                                    'BAPH_REDIRECT_ON_SIGNOUT',
                                    None)

BAPH_SIGNIN_REDIRECT_URL = getattr(settings,
                                      'BAPH_SIGNIN_REDIRECT_URL',
                                      '/')

BAPH_ACTIVATION_REQUIRED = getattr(settings,
                                      'BAPH_ACTIVATION_REQUIRED',
                                      True)

BAPH_ACTIVATION_DAYS = getattr(settings,
                                  'BAPH_ACTIVATION_DAYS',
                                  7)

BAPH_ACTIVATION_NOTIFY = getattr(settings,
                                    'BAPH_ACTIVATION_NOTIFY',
                                    True)

BAPH_ACTIVATION_NOTIFY_DAYS = getattr(settings,
                                         'BAPH_ACTIVATION_NOTIFY_DAYS',
                                         5)

BAPH_ACTIVATION_RETRY = getattr(settings,
                                    'BAPH_ACTIVATION_RETRY',
                                    False)

BAPH_ACTIVATED = getattr(settings,
                            'BAPH_ACTIVATED',
                            'ALREADY_ACTIVATED')

BAPH_REMEMBER_ME_DAYS = getattr(settings,
                                   'BAPH_REMEMBER_ME_DAYS',
                                   (gettext('a month'), 30))

BAPH_FORBIDDEN_USERNAMES = getattr(settings,
                                      'BAPH_FORBIDDEN_USERNAMES',
                                      ('signup', 'signout', 'signin',
                                       'activate', 'me', 'password'))

BAPH_USE_HTTPS = getattr(settings,
                            'BAPH_USE_HTTPS',
                            False)

BAPH_MUGSHOT_GRAVATAR = getattr(settings,
                                   'BAPH_MUGSHOT_GRAVATAR',
                                   True)

BAPH_MUGSHOT_GRAVATAR_SECURE = getattr(settings,
                                          'BAPH_MUGSHOT_GRAVATAR_SECURE',
                                          BAPH_USE_HTTPS)

BAPH_MUGSHOT_DEFAULT = getattr(settings,
                                  'BAPH_MUGSHOT_DEFAULT',
                                  'identicon')

BAPH_MUGSHOT_SIZE = getattr(settings,
                               'BAPH_MUGSHOT_SIZE',
                               80)

BAPH_MUGSHOT_CROP_TYPE = getattr(settings,
                                    'BAPH_MUGSHOT_CROP_TYPE',
                                    'smart')

BAPH_MUGSHOT_PATH = getattr(settings,
                               'BAPH_MUGSHOT_PATH',
                               'mugshots/')

BAPH_DEFAULT_PRIVACY = getattr(settings,
                                  'BAPH_DEFAULT_PRIVACY',
                                  'registered')

BAPH_DISABLE_PROFILE_LIST = getattr(settings,
                                       'BAPH_DISABLE_PROFILE_LIST',
                                       False)

BAPH_USE_MESSAGES = getattr(settings,
                               'BAPH_USE_MESSAGES',
                               True)

BAPH_LANGUAGE_FIELD = getattr(settings,
                                 'BAPH_LANGUAGE_FIELD',
                                 'language')

BAPH_AUTH_WITHOUT_USERNAMES = getattr(settings,
                                    'BAPH_AUTH_WITHOUT_USERNAMES',
                                    False)

BAPH_AUTH_UNIQUE_WITHIN_ORG = getattr(settings,
                                  'BAPH_AUTH_UNIQUE_WITHIN_ORG',
                                  False)


BAPH_PROFILE_DETAIL_TEMPLATE = getattr(
    settings, 'BAPH_PROFILE_DETAIL_TEMPLATE', 'BAPH/profile_detail.html')

BAPH_PROFILE_LIST_TEMPLATE = getattr(
    settings, 'BAPH_PROFILE_LIST_TEMPLATE', 'BAPH/profile_list.html')

BAPH_HIDE_EMAIL = getattr(settings, 'BAPH_HIDE_EMAIL', False)
