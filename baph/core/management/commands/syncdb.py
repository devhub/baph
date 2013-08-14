# -*- coding: utf-8 -*-
from optparse import make_option
import traceback

from django.conf import settings
from django.core.management import call_command
from django.core.management.color import no_style
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from sqlalchemy import MetaData, create_engine
from sqlalchemy.schema import CreateSchema, DropSchema, CreateTable

from baph.core.management.base import NoArgsCommand
from baph.core.management.sql import emit_post_sync_signal
from baph.db import connections, Session, DEFAULT_DB_ALIAS
from baph.db.models import Base, signals, get_apps, get_models


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
        make_option('--no-initial-data', action='store_false', dest='load_initial_data', default=True,
            help='Tells Django not to load any initial data after database synchronization.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to synchronize. '
                'Defaults to the "default" database.'),
    )
    help = "Create the database tables for all apps in INSTALLED_APPS whose tables haven't already been created."

    def handle_noargs(self, **options):

        verbosity = int(options.get('verbosity'))
        interactive = options.get('interactive')
        show_traceback = options.get('traceback')
        load_initial_data = options.get('load_initial_data')

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

        db = options.get('database')
        engine = connections[db]
        default_schema = engine.url.database

        # the default db may not exist yet, so we remove it before connecting
        engine.url.database = None
        tmp_url = str(engine.url)
        engine.url.database = default_schema
        tmp_engine = create_engine(tmp_url)
        tmp_conn = tmp_engine.connect()
        existing_schemas = set([s[0] for s in tmp_conn.execute('show databases')])
        if not default_schema in existing_schemas:
            tmp_engine.execute(CreateSchema(default_schema))
            existing_schemas.add(default_schema)

        # now reconnect with the default_db provided
        conn = engine.connect()
        Base.metadata.bind = engine
        
        if verbosity >= 3:
            self.stdout.write("Getting existing schemas...\n")
            for schema in existing_schemas:
                self.stdout.write("\t%s\n" % schema)
            else:
                self.stdout.write("\tNone\n")

        existing_tables = []
        if verbosity >= 1:
            self.stdout.write("Getting existing tables...\n")
        for schema in existing_schemas:
            for name in engine.engine.table_names(schema, connection=conn):
                existing_tables.append('%s.%s' % (schema,name))
                if verbosity >= 3:
                    self.stdout.write("\t%s.%s\n" % (schema,name))    

        existing_models = []
        if verbosity >= 1:
            self.stdout.write("Getting existing models...\n")
        for cls_name, cls in Base._decl_class_registry.items():
            tablename = get_tablename(cls)
            if tablename and tablename in existing_tables:
                existing_models.append(cls)
                if verbosity >= 3:
                    self.stdout.write("\t%s\n" % cls)

        all_tables = []
        if verbosity >= 1:
            self.stdout.write("Getting required tables...\n")
        for table in Base.metadata.sorted_tables:
            tablename = get_tablename(table)
            all_tables.append(tablename)
            if verbosity >= 3:
                self.stdout.write("\t%s\n" % tablename)

        all_models = []
        if verbosity >= 1:
            self.stdout.write("Getting required models...\n")
        for app in get_apps():
            for model in get_models(app, include_auto_created=True):
                app_name = app.__name__.rsplit('.',1)[0]
                all_models.append( (app_name, model) )
                if verbosity >= 3:
                    self.stdout.write("\t%s.%s\n" % (app_name,model))

        schema_manifest = set()
        table_manifest = set()
        if verbosity >= 1:
            self.stdout.write('Building manifest...\n')
        for app_name, model in all_models:
            tablename = get_tablename(model)
            if tablename in existing_tables:
                continue
            table_manifest.add( (app_name, model) )
            schema = tablename.rsplit('.',1)[0]
            if schema not in existing_schemas:
                schema_manifest.add(schema)

        table_manifest = sorted(table_manifest, key=lambda x: 
            all_tables.index(get_tablename(x[1])))

        if verbosity >= 3:
            print 'Schema Manifest:\n'
            for schema in schema_manifest:
                print '\t%s\n' % schema
            print 'Model/Table Manifest\n'
            for app_name, model in table_manifest:
                print '\t%s.%s (%s)\n' % (app_name, model._meta.object_name, 
                    get_tablename(model)) 

        # create any missing schemas
        if verbosity >= 1:
            self.stdout.write("Creating schemas ...\n")
        for schema in schema_manifest:
            if verbosity >= 3:
                self.stdout.write("\t%s\n" % schema)
            engine.execute(CreateSchema(schema))
            existing_schemas.add(schema)            

        # create any missing tables
        created_models = set()
        if verbosity >= 1:
            self.stdout.write("Creating tables ...\n")
        for app_name, model in table_manifest:
            if verbosity >= 3:
                self.stdout.write("\tCreating table for model %s.%s\n" 
                    % (app_name, model._meta.object_name))
            tablename = get_tablename(model)
            if tablename not in existing_tables:
                model.__table__.create()
                existing_tables.append(tablename)
            existing_models.append(model)
            created_models.add(model)

        # Send the post_syncdb signal
        emit_post_sync_signal(created_models, verbosity, interactive, db)

        # Load initial_data fixtures (unless that has been disabled)
        if load_initial_data:
            call_command('loaddata', 'initial_data', verbosity=verbosity,
                         database=db, skip_validation=True)


