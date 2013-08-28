# -*- coding: utf-8 -*-
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.color import no_style
from django.utils.importlib import import_module

from baph.core.management.base import NoArgsCommand, CommandError
from baph.core.management.sql import emit_post_sync_signal #, sql_flush
from baph.db import ORM, DEFAULT_DB_ALIAS
from baph.db.models import signals, get_apps, get_models


orm = ORM.get()
Base = orm.Base

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to flush. '
                'Defaults to the "default" database.'),
    )
    help = "Executes ``sqlflush`` on the current database."

    def handle_noargs(self, **options):
        #db = options.get('database', DEFAULT_DB_ALIAS)
        #connection = connections[db]
        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive')

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
            try:
                import_module('.management', app_name)
            except ImportError:
                pass

        #sql_list = sql_flush(self.style, connection, only_django=True)

        if interactive:
            confirm = raw_input("""You have requested a flush of the database.
This will IRREVERSIBLY DESTROY all data currently in the database,
and return each table to the state it was in after syncdb.
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """)
        else:
            confirm = 'yes'

        if confirm == 'yes':
            session = orm.sessionmaker()
            session.execute('SET foreign_key_checks=0')

            try:
                for table in reversed(Base.metadata.sorted_tables):
                    if table.name == 'baph_auth_permissions':
                        # TODO: this is terrible, fix it
                        continue
                    session.execute(table.delete())
                session.commit()
                session.execute('SET foreign_key_checks=1')
            except Exception, e:
                session.rollback()
                session.execute('SET foreign_key_checks=1')
                raise
                raise CommandError("""Database couldn't be flushed. Possible reasons:
  * The database isn't running or isn't configured correctly.
  * At least one of the expected database tables doesn't exist.
  * The SQL was invalid.
Hint: Look at the output of 'django-admin.py sqlflush'. That's the SQL this command wasn't able to run.
The full error: %s""")

            # Emit the post sync signal. This allows individual
            # applications to respond as if the database had been
            # sync'd from scratch.
            all_models = []
            for app in get_apps():
                all_models.extend([
                    m for m in get_models(app, include_auto_created=True)
                ])
            emit_post_sync_signal(set(all_models), verbosity, interactive, None) 

            # Reinstall the initial_data fixture.
            if options.get('load_initial_data'):
                # Reinstall the initial_data fixture.
                call_command('loaddata', 'initial_data', **options)

        else:
            self.stdout.write("Flush cancelled.\n")
