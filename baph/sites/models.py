# -*- coding: utf-8 -*-
'''\
:mod:`baph.sites.models` -- The "sites" framework SQLAlchemy models
===================================================================
'''

from baph.db.models import Model
from baph.db.orm import ORM
from baph.decorators.db import sqlalchemy_session
from baph.utils.importing import import_attr
RequestSite = import_attr(['django.contrib.sites.models'], 'RequestSite')
from sqlalchemy import Column, Integer, String, Unicode

__all__ = ['orm', 'RequestSite', 'Site']

orm = ORM.get()
SITE_CACHE = {}


class Site(orm.Base, Model):
    '''A port of :class:`django.contrib.sites.models.Site`.'''
    __tablename__ = 'django_site'

    id = Column(Integer, primary_key=True)
    '''The ID corresponding to the :setting:`SITE_ID` of the given site.'''
    domain = Column(String(255), nullable=False)
    '''The full, ASCII domain name of the site.'''
    name = Column(Unicode(64), nullable=False)
    '''The human-readable, English name of the site.'''

    def __unicode__(self):
        return self.domain

    @sqlalchemy_session
    def save(self, session=None):
        '''Commits the changes to the :class:`Site` and invalidates the cached
        version, if any.
        '''
        session.commit()
        if self.id in SITE_CACHE:
            del SITE_CACHE[self.id]

    @sqlalchemy_session
    def delete(self, session=None):
        '''Deletes the object from the database and the cache, if necessary.'''
        pk = self.id
        session.delete(self)
        session.commit()
        if pk in SITE_CACHE:
            del SITE_CACHE[pk]

    @classmethod
    @sqlalchemy_session
    def get_current(cls, session=None):
        '''Returns the current :class:`Site` based on the :setting:`SITE_ID`
        in the project's settings. The :class:`Site` object is cached the
        first time it's retrieved from the database.
        '''
        from django.conf import settings
        sid = getattr(settings, 'SITE_ID', None)
        if sid is None:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('''\
You're using the Django "sites framework" without having set the SITE_ID
setting. Create a site in your database and set the SITE_ID setting to fix
this error.''')
        current_site = SITE_CACHE.get(sid)
        if not current_site:
            current_site = session.query(cls).get(sid)
            SITE_CACHE[sid] = current_site
        return current_site

    @staticmethod
    def clear_cache():
        '''Clears the :class:`Site` object cache.'''
        global SITE_CACHE
        SITE_CACHE = {}


@sqlalchemy_session
def get_current_site(request, session=None):
    '''Checks if :mod:`baph.sites` is installed and returns either the current
    :class:`Site` object or a :class:`RequestSite` object based on the request.
    '''
    if Site.__table__.exists():
        current_site = Site.get_current(session=session)
    else:
        current_site = RequestSite(request)
    return current_site
