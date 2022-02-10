# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.sites.models import get_current_site, orm, RequestSite, Site
from baph.test.base import TestCase
from django.conf import settings
from django.http import HttpRequest


class SitesTestCase(TestCase):
    '''Tests baph.sites.'''

    @classmethod
    def setUpClass(cls):
        Site.__table__.create()
        cls.session = orm.sessionmaker()

    @classmethod
    def tearDownClass(cls):
        Site.__table__.drop()

    def setUp(self):
        if not Site.__table__.exists():
            Site.__table__.create()
        site = Site(id=settings.SITE_ID, domain='example.com',
                    name=u'example.com')
        self.session.add(site)
        self.session.commit()

    def tearDown(self):
        if Site.__table__.exists():
            site = self.session.query(Site).get(settings.SITE_ID)
            if site:
                self.session.delete(site)
                self.session.commit()

    def test_get_current(self):
        '''Make sure that get_current() does not return a deleted Site object.
        '''
        site = Site.get_current(session=self.session)
        self.assertIsInstance(site, Site)

        site.delete(session=self.session)
        self.assertIsNone(Site.get_current(session=self.session))

    def test_site_cache(self):
        '''After updating a ``Site`` object, we shouldn't return a bogus value
        from the ``SITE_CACHE``.
        '''
        site = Site.get_current(session=self.session)
        self.assertEqual(site.name, u'example.com')
        site2 = self.session.query(Site).get(settings.SITE_ID)
        site2.name = u'Example site'
        site2.save()
        site = Site.get_current(session=self.session)
        self.assertEqual(site.name, u'Example site')

    def test_get_current_site(self):
        '''Test that the correct Site object is returned.'''
        request = HttpRequest()
        request.META = {
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '80',
        }
        site = get_current_site(request)
        self.assertIsInstance(site, Site)
        self.assertEqual(site.id, settings.SITE_ID)

        # Test that an exception is raised if the sites framework is installed
        # but there is no matching Site
        site.delete(session=self.session)
        self.assertIsNone(get_current_site(request))

        # A RequestSite is returned if the sites framework is not installed
        Site.__table__.drop()
        site = get_current_site(request)
        self.assertIsInstance(site, RequestSite)
        self.assertEqual(site.name, u'example.com')
