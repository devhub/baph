# -*- coding: utf8 -*-
'''
:mod:`baph.socialmedia.facebook` -- Facebook integration
========================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>

Handles retrieving and sending data from/to Facebook.
'''

from __future__ import absolute_import

from django.conf import settings
from django.core.urlresolvers import reverse
import facebook
import urllib

OAUTH_AUTHORIZE_URI = 'https://graph.facebook.com/oauth/authorize'


class Facebook(object):
    '''Convenience class for accessing data from the Facebook Graph API.

    :param token: The OAuth access token given by Facebook.
    :type token: :class:`str`
    '''

    def __init__(self, token):
        self._token = token
        self._fql = facebook.FQLAPI(token)
        self._graph = facebook.GraphAPI(token)
        self._user = self._graph.get_object('me')

    @staticmethod
    def get_authorization_url(request, view, *args, **kwargs):
        url = request.build_absolute_uri(reverse(view, args=args,
                                                 kwargs=kwargs))
        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'display': 'popup',
            'redirect_uri': url,
            'scope': getattr(settings, 'FACEBOOK_EXTRA_PERMISSIONS', ''),
            'type': 'user_agent',
        }
        return '%s?%s' % (OAUTH_AUTHORIZE_URI, urllib.urlencode(params))

    @property
    def user(self):
        '''Retrieves data from the Facebook user's profile.

        :rtype: :class:`dict`
        '''
        return self._user

    def get_page(self, page_id):
        '''Retrieves data from the given Facebook page ID.

        :param page_id: The ID of the Facebook page.
        :type page_id: :class:`str`
        :rtype: :class:`dict`
        '''
        return self._graph.get_object(page_id)

    @property
    def admin_pages(self):
        '''Retrieves all of the pages that a user has administrative
        privileges for.

        :rtype: :class:`dict` (key: page ID, value: page)
        '''
        query = '''\
SELECT page_id, name, page_url FROM page WHERE page_id IN (
    SELECT page_id FROM page_admin WHERE uid=%s
)''' % self._user['id']
        result = self._fql.query(query)
        try:
            pages = dict([(p['page_id'], p['name'])  for p in result['page']])
        except KeyError:
            pages = {}
        return pages

    @classmethod
    def has_permission(cls, permission):
        if not hasattr(cls, 'permissions'):
            cls.permissions = settings.FACEBOOK_EXTRA_PERMISSIONS.split(',')
        return permission in cls.permissions

    def get_friends(self, limit=None):
        '''Retrieves the friends from a user.

        :param limit: The maximum number of friends to retrieve.
        :type limit: :class:`int`
        :rtype: :class:`list` of :class:`dict`
        '''
        if not self.has_permission('read_stream'):
            return False
        kwargs = {}
        if limit is not None:
            kwargs['limit'] = limit
        return self._graph.get_connections('me', 'friends', **kwargs)['data']

    def get_wall_posts(self, limit=None):
        '''Retrieves messages from the user's wall.

        :param limit: The maximum number of wall posts to retrieve.
        :type limit: :class:`int`
        :rtype: :class:`list` of :class:`dict`
        '''
        kwargs = {}
        if limit is not None:
            kwargs['limit'] = limit
        return self._graph.get_connections('me', 'feed', **kwargs)['data']

    def _do_post(self, obj, message, link=None, image=None, description=None,
                     caption=None):
        if not self.has_permission('publish_stream'):
            return False
        kwargs = {}
        if link is not None:
            # TODO make sure it's a link
            kwargs['link'] = link
        if image is not None:
            # TODO make sure it's a URI
            kwargs['picture'] = image
        if description is not None:
            kwargs['description'] = description
        if caption is not None:
            kwargs['caption'] = caption
        return self._graph.put_object(obj, 'feed', message=message,
                                      **kwargs)

    def post_to_wall(self, message, link=None, image=None, description=None,
                     caption=None):
        '''Posts a message to the user's wall.

        :param message: The message to put in the post.
        :type message: :class:`unicode`
        :param link: A URI associated with the post (optional).
        :type link: :class:`unicode` or :const:`None`
        :param image: An image URI associated with the post (optional).
        :type image: :class:`unicode` or :const:`None`
        :param description: A description (usually of the URI) to put in the
                            post (optional).
        :type description: :class:`unicode` or :const:`None`
        :param caption: A description (usually of the image) to put in the
                        post (optional).
        :type caption: :class:`unicode` or :const:`None`
        '''
        return self._do_post('me', message, link=link, image=image,
                             description=description, caption=caption)

    def post_to_page(self, page_id, message, link=None, image=None,
                     description=None, caption=None):
        '''Posts a message to a page's wall.

        :param page_id: The ID of the Facebook page to post to.
        :type page_id: :class:`str`
        :param message: The message to put in the post.
        :type message: :class:`unicode`
        :param link: A URI associated with the post (optional).
        :type link: :class:`unicode` or :const:`None`
        :param image: An image URI associated with the post (optional).
        :type image: :class:`unicode` or :const:`None`
        :param description: A description (usually of the URI) to put in the
                            post (optional).
        :type description: :class:`unicode` or :const:`None`
        :param caption: A description (usually of the image) to put in the
                        post (optional).
        :type caption: :class:`unicode` or :const:`None`
        '''
        return self._do_post(page_id, message, link=link, image=image,
                             description=description, caption=caption)
