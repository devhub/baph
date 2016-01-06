import sys
import os
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.color import no_style
from django.utils.importlib import import_module

from baph.auth.management import create_permissions
from baph.auth.models import Permission, PermissionAssociation
from baph.core.management.base import NoArgsCommand, CommandError
from baph.db.models import get_apps
from baph.db.orm import ORM


orm = ORM.get()

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--flush', action='store_true', dest='flush', 
            default=False,
            help='Flushes all existing permissions before population'),
    )

    def handle_noargs(self, **options):
        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive')
        flush = options.get('flush')
        self.style = no_style()

        if flush:
            # clear existing permissions
            session = orm.sessionmaker()
            session.execute(Permission.__table__.delete())
            session.commit()
        
        session = orm.sessionmaker()
        for app in get_apps():
            create_permissions(app, [], verbosity)
        session.commit()