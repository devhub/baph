# -*- coding: utf-8 -*-
from optparse import make_option
import sys
import traceback

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
#from django.core.management.sql import custom_sql_for_model, emit_post_sync_signal
from django.dispatch import Signal
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from sqlalchemy import MetaData, inspect
from sqlalchemy.engine import reflection
from sqlalchemy.schema import CreateSchema, DropSchema, CreateTable, DropTable, DropConstraint, ForeignKeyConstraint, Table, MetaData

from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import signals, get_apps, get_models
from baph.db.orm import ORM


post_syncdb = Signal(providing_args=["class", "app", "created_models", 
    "verbosity", "interactive", "db"])

def get_tablename(obj):
    if hasattr(obj, '__table__'):
        " this is a class "
        table = obj.__table__
        schema = table.schema or obj.metadata.bind.url.database
        name = table.name
    elif hasattr(obj, 'schema'):
        " this is a table "
        schema = obj.schema or obj.metadata.bind.url.database
        name = obj.name
    else:
        return None
    return '%s.%s' % (schema, name)


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to purge. '
                'Defaults to the "default" database.'),
    )
    help = "Delete the database tables and schemas for all apps in INSTALLED_APPS."

    def handle_noargs(self, **options):
        verbosity = 1 #int(options.get('verbosity'))
        interactive = options.get('interactive')
        show_traceback = options.get('traceback')

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
            try:
                import_module('.management', app_name)
            except ImportError as exc:
                # This is slightly hackish. We want to ignore ImportErrors
                # if the "management" module itself is missing -- but we don't
                # want to ignore the exception if the management module exists
                # but raises an ImportError for some reason. The only way we
                # can do this is to check the text of the exception. Note that
                # we're a bit broad in how we check the text, because different
                # Python implementations may not use the same text.
                # CPython uses the text "No module named management"
                # PyPy uses "No module named myproject.myapp.management"
                msg = exc.args[0]
                if not msg.startswith('No module named') or 'management' not in msg:
                    raise

        if interactive:
            confirm = raw_input("""You have requested a purghe of the database.
This will IRREVERSIBLY DESTROY all data currently in the database,
and DELETE ALL TABLES AND SCHEMAS. Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """)
        else:
            confirm = 'yes'

        if confirm == 'yes':
            db = options.get('database')
            orm = ORM.get(db)
            engine = orm.engine
            conn = engine.connect()
            Base = orm.Base

            default_schema = engine.url.database
            existing_schemas = set([s[0] for s in conn.execute('show databases') 
                               if s[0]])
            schemas = set([default_schema])
            schemas.update(Base.metadata._schemas)
            schemas = schemas.intersection(existing_schemas)

            existing_tables = []
            if verbosity >= 1:
                self.stdout.write("Getting existing tables...\n")
            for schema in schemas:
                if schema not in existing_schemas:
                    schemas.remove(schema)
                    continue
                for name in engine.engine.table_names(schema, connection=conn):
                    existing_tables.append('%s.%s' % (schema,name))
                    if verbosity >= 3:
                        self.stdout.write("\t%s.%s\n" % (schema,name))    

            inspector = reflection.Inspector.from_engine(engine)
            metadata = MetaData()
            all_fks = []
            tables = []
            for table in Base.metadata.tables.values():
                schema = table.schema or default_schema
                table_name = table.name
                table_fullname = '%s.%s' % (schema, table_name)
                if table_fullname not in existing_tables:
                    continue

                fks = []
                for fk in inspector.get_foreign_keys(table_name, schema):
                    if not fk['name']:
                        continue
                    fks.append(ForeignKeyConstraint((), (), name=fk['name']))
                t = Table(table_name, metadata, *fks, schema=table.schema)
                tables.append(t)
                all_fks.extend(fks)

            for fkc in all_fks:
                conn.execute(DropConstraint(fkc))

            for table in tables:
                conn.execute(DropTable(table))

            for schema in schemas:
                conn.execute(DropSchema(schema))
        else:
            self.stdout.write("Purge cancelled.\n")

