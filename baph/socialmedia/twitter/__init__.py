# -*- coding: utf-8 -*-
'''
:mod:`baph.socialmedia.twitter` -- Twitter integration
========================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

Handles retrieving and sending data from/to Twitter.
'''

from django.conf import settings
from django.core.urlresolvers import reverse
import tweepy

SESSION_KEY = 'twitter_oauth_request_token'


class TwitterToken(object):
    '''Represents a Twitter access or request token.'''

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


class TwitterRequestToken(TwitterToken):
    '''Represents a Twitter request token.'''


class TwitterAccessToken(TwitterToken):
    '''Represents a Twitter access token.'''


class Twitter(object):
    '''Convenience class for the Twitter API.

    :param access_token: The OAuth access token provided by Twitter for a
                         given user.
    :type access_token: :class:`TwitterToken` or :const:`None`
    '''

    def __init__(self, token=None):
        self._key = settings.TWITTER_CONSUMER_KEY
        self._secret = settings.TWITTER_CONSUMER_SECRET
        self._auth = tweepy.OAuthHandler(self._key, self._secret)
        if token:
            if isinstance(token, TwitterAccessToken):
                self._auth.set_access_token(token.key, token.secret)
            elif isinstance(token, TwitterRequestToken):
                self._auth.set_request_token(token.key, token.secret)
            self._api = tweepy.API(self._auth)

    @property
    def api(self):
        '''The Tweepy API object.'''
        if not hasattr(self, '_api'):
            self._api = tweepy.API(self._auth)
        return self._api

    @property
    def auth(self):
        '''Twitter authentication information.'''
        return self._auth

    @property
    def username(self):
        '''The user's Twitter username.'''
        return self._auth.get_username()

    @property
    def user(self):
        '''The Tweepy user object.'''
        return self.api.me()

    @staticmethod
    def full_url_lookup(request, view, *args, **kwargs):
        return request.build_absolute_uri(reverse(view, args=args,
                                                  kwargs=kwargs))

    def get_authorization_url(self, request, *args, **kwargs):
        signin = kwargs.pop('signin_with_twitter', False)
        request_uri = self.full_url_lookup(request, *args, **kwargs)
        self._auth = tweepy.OAuthHandler(self._key, self._secret, request_uri)
        return self._auth.get_authorization_url(signin_with_twitter=signin)

    def set_request_token(self, request, *args, **kwargs):
        '''Sets the OAuth request token for the current user.'''
        try:
            auth_uri = self.get_authorization_url(request, *args, **kwargs)
            request_token = self._auth.request_token
            request.session[SESSION_KEY] = \
                TwitterRequestToken(request_token.key, request_token.secret)
            return auth_uri
        except tweepy.TweepError:
            return '#'

    def get_access_token(self, verifier):
        try:
            token = self._auth.get_access_token(verifier)
        except tweepy.TweepError:
            return None
        else:
            return TwitterAccessToken(key=token.key, secret=token.secret)

    def get_timeline(self, limit=None):
        '''Retrieves the timeline of the current user.

        :param limit: The maximum number of statuses to retrieve.
        :type limit: :class:`int` or :const:`None`
        '''
        return self.api.user_timeline(count=limit)

    def post_status(self, status):
        '''Posts a Twitter status for the current user.

        :param message: The message to post.
        :type message: :class:`unicode`
        :returns: :const:`True` on success, :const:`False` on failure.
        :rtype: :class:`bool`
        '''
        if not hasattr(self, '_api'):
            return False
        try:
            self._api.update_status(status)
        except tweepy.TweepError:
            if settings.DEBUG:
                raise
            else:
                return False
        return True
