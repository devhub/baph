from optparse import make_option

from django.conf import settings
from django.db import connections, router, transaction, DEFAULT_DB_ALIAS
from django.core.management import call_command
from django.core.management.color import no_style
from django.core.management.sql import sql_flush, emit_post_sync_signal
from django.utils.importlib import import_module

from baph.core.management.base import NoArgsCommand, CommandError
from baph.db.orm import ORM, Base


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
            try:
                orm = ORM.get()
                session = orm.sessionmaker()
                for table in reversed(Base.metadata.sorted_tables):
                    if table.name == 'baph_auth_permissions':
                        # TODO: this is terrible, fix it
                        continue
                    try:
                        session.execute(table.delete())
                    except:
                        pass
                session.commit()
            except Exception, e:
                session.rollback()
                raise
                raise CommandError("""Database couldn't be flushed. Possible reasons:
  * The database isn't running or isn't configured correctly.
  * At least one of the expected database tables doesn't exist.
  * The SQL was invalid.
Hint: Look at the output of 'django-admin.py sqlflush'. That's the SQL this command wasn't able to run.
The full error: %s""")

            # Reinstall the initial_data fixture.
            kwargs = options.copy()
            #kwargs['database'] = db
            call_command('loaddata', 'initial_data', **kwargs)

        else:
            print "Flush cancelled."
