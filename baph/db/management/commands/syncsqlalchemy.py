# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.db.orm import ORM
from baph.utils.importing import import_any_module
from django.conf import settings
from django.core.management.base import NoArgsCommand

orm = ORM.get()


class Command(NoArgsCommand):
    help = u'Create the database tables for all apps in INSTALLED_APPS ' \
           u'whose models are written with SQLAlchemy and whose tables ' \
           u'have not already been created.'
    requires_model_validation = False

    def handle_noargs(self, **kwargs):
        for app in settings.INSTALLED_APPS:
            import_any_module(['%s.models' % app], raise_error=False)
        if len(orm.metadata.tables) > 0:
            orm.metadata.create_all()
