# -*- coding: utf-8 -*-
from copy import deepcopy

from django.conf import settings
from django.core.management import call_command
from django.core.management.color import no_style
from django.utils.importlib import import_module
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import CreateSchema, CreateTable

from baph.core.management.new_base import BaseCommand
from baph.core.management.sql import emit_post_sync_signal
from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import get_apps, get_models
from baph.db.orm import ORM, Base
from baph.db.utils import get_tablename


class Command(BaseCommand):
    help = "Create the database tables for all apps in INSTALLED_APPS whose " \
           "tables haven't already been created."

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', action='store_false', dest='interactive',
            default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'
        )
        parser.add_argument(
            '--no-initial-data', action='store_false', dest='load_initial_data',
            default=True,
            help='Tells Django not to load any initial data after database synchronization.'
        )
        parser.add_argument(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to synchronize. '
                'Defaults to the "default" database.'
        )

    def handle(self, **options):
        verbosity = int(options.get('verbosity'))
        interactive = options.get('interactive')
        show_traceback = options.get('traceback')
        load_initial_data = options.get('load_initial_data')

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
            try:
                import_module('.models', app_name)
            except ImportError as exc:
                pass

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
        orm = ORM.get(db)

        default_schema = orm.engine.url.database
        app_schemas = set(orm.Base.metadata._schemas)
        app_schemas.add(default_schema)

        url = deepcopy(orm.engine.url)
        url.database = None
        engine = create_engine(url)
        inspector = inspect(engine)

        # get a list of existing schemas
        existing_schemas = set(inspector.get_schema_names())
        existing_schemas = app_schemas.intersection(existing_schemas)
        if not default_schema in existing_schemas:
            engine.execute(CreateSchema(default_schema))
            existing_schemas.add(default_schema)

        required_schemas = app_schemas - existing_schemas

        engine = orm.engine
        conn = engine.connect()
        Base.metadata.bind = engine
        
        if verbosity >= 3:
            self.stdout.write("Getting existing schemas...\n")
            for schema in existing_schemas or [None]:
                self.stdout.write("\t%s\n" % schema)

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

        required_tables = []
        if verbosity >= 1:
            self.stdout.write("Getting required tables...\n")
        for table in Base.metadata.sorted_tables:
            tablename = get_tablename(table)
            if verbosity >= 3:
                self.stdout.write("\t%s\n" % tablename)
            if tablename not in existing_tables:
                required_tables.append(table)

        required_models = []
        if verbosity >= 1:
            self.stdout.write("Getting required models...\n")
        for app in get_apps():
            app_name = app.__name__.rsplit('.',1)[0]
            for model in get_models(app, include_auto_created=True):
                tablename = get_tablename(model)
                if verbosity >= 3:
                    self.stdout.write("\t%s.%s\n" % (app_name, model.__name__))
                if tablename not in existing_tables:
                    required_models.append( (app_name, model) )

        if verbosity >= 3:
            self.stdout.write('Schema Manifest:\n')
            for schema in required_schemas:
                self.stdout.write('\t%s\n' % schema)
            self.stdout.write('Model/Table Manifest\n')
            for app_name, model in required_models:
                self.stdout.write('\t%s.%s (%s)\n' % (app_name, model._meta.object_name, 
                    get_tablename(model)))

        # create any missing schemas
        if verbosity >= 1:
            self.stdout.write("Creating schemas ...\n")
        for schema in required_schemas:
            if verbosity >= 3:
                self.stdout.write("\t%s\n" % schema)
            engine.execute(CreateSchema(schema))
            existing_schemas.add(schema)            

        # create any missing tables
        if verbosity >= 1:
            self.stdout.write("Creating tables ...\n")
        for app_name, model in required_models:
            if verbosity >= 3:
                self.stdout.write("\tCreating table for model %s.%s\n" 
                    % (app_name, model._meta.object_name))

        orm.Base.metadata.create_all(bind=engine, tables=required_tables)

        # Send the post_syncdb signal
        created_models = [x[1] for x in required_models]
        emit_post_sync_signal(created_models, verbosity, interactive, db)

        # Load initial_data fixtures (unless that has been disabled)
        if load_initial_data:
            call_command('loaddata', 'initial_data', verbosity=verbosity,
                         database=db, skip_validation=True)
