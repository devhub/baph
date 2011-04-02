# -*- coding: utf-8 -*-
'''
A management command which deletes expired accounts (e.g., accounts which
signed up but never activated) from the database.

Calls :func:`RegistrationProfile.delete_expired_users`, which
contains the actual logic for determining which accounts are deleted.
'''

from baph.auth.registration.models import RegistrationProfile
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    help = "Delete expired user registrations from the database"

    def handle_noargs(self, **options):
        RegistrationProfile.delete_expired_users()
