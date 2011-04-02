# -*- coding: utf-8 -*-

from baph.auth.models import orm, User
from baph.piston.models import Consumer
from baph.test.base import BaseTestCase
from coffin.shortcuts import render_to_string
from django.conf import settings
from django.core import mail
from jinja2 import TemplateNotFound


class ConsumerTest(BaseTestCase):
    '''Tests the OAuth Consumer model for :mod:`baph.piston`.'''

    @classmethod
    def setUpClass(cls):
        super(ConsumerTest, cls).setUpClass()
        cls.session = orm.sessionmaker()

    def setUp(self):
        self.cuser = User.create_user('testconsumer',
                                     'testconsumer@example.com')
        data = dict(name=u'Piston Test Consumer',
                    description=u'A test consumer for Piston.',
                    session=self.session, user=self.cuser)
        self.consumer = Consumer.create(**data)
        mail.outbox = []

    def tearDown(self):
        self.session.delete(self.cuser)
        self.session.delete(self.consumer)
        self.session.commit()

    @classmethod
    def tearDownClass(cls):
        super(ConsumerTest, cls).tearDownClass()
        cls.session.close()
        orm.sessionmaker_remove()

    def _pre_test_email(self):
        template = 'piston/mails/consumer_%s.txt' % self.consumer.status
        try:
            render_to_string(template, {
                'consumer': self.consumer,
                'user': self.cuser,
            })
            return True
        except TemplateNotFound:
            '''They haven't set up the templates, which means they might not
            want these emails sent.
            '''
            return False

    def test_create_pending(self):
        '''Ensure creating a pending Consumer sends proper emails.'''
        # Verify if the emails can be sent
        if not self._pre_test_email():
            return

        # If it's pending we should have two messages in the outbox; one
        # to the consumer and one to the site admins.
        if len(settings.ADMINS):
            self.assertEquals(len(mail.outbox), 2)
        else:
            self.assertEquals(len(mail.outbox), 1)

        expected = "Your API Consumer for example.com is awaiting approval."
        self.assertEquals(mail.outbox[0].subject, expected)

    def test_delete_consumer(self):
        '''Ensure deleting a Consumer sends a cancel email.'''

        # Delete the consumer, which should fire off the cancel email.
        self.session.delete(self.consumer)

        # Verify if the emails can be sent
        if not self._pre_test_email():
            return

        self.assertEquals(len(mail.outbox), 1)
        expected = "Your API Consumer for example.com has been canceled."
        self.assertEquals(mail.outbox[0].subject, expected)
