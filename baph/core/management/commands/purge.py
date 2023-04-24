# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from copy import deepcopy
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
from sqlalchemy import MetaData, inspect, create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.schema import (CreateSchema, DropSchema,
  CreateTable, DropTable, DropConstraint,
  ForeignKeyConstraint, Table, MetaData)

from baph.core.management.new_base import BaseCommand
from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import signals, get_apps, get_models
from baph.db.orm import ORM
from six.moves import input


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


class Command(BaseCommand):
  help = "Delete the database tables and schemas for all apps in INSTALLED_APPS."

  def add_arguments(self, parser):
    parser.add_argument(
      '--noinput', action='store_false', dest='interactive',
      default=True,
      help='Tells Django to NOT prompt the user for input of any kind.'
    )
    parser.add_argument(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a database to purge. '
      'Defaults to the "default" database.'
    )

  def handle(self, **options):
    verbosity = 1 #int(options.get('verbosity'))
    interactive = options.get('interactive')
    show_traceback = options.get('traceback')

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
    db_info = orm.settings_dict
    is_test_db = db_info.get('TEST', False)
    if not is_test_db:
      print('Database "%s" cannot be purged because it is not a test ' \
            'database.\nTo flag this as a test database, set TEST to ' \
            'True in the database settings.' % db)
      sys.exit()

    if interactive:
      confirm = input('\nYou have requested a purge of database ' \
          '"%s" (%s). This will IRREVERSIBLY DESTROY all data ' \
          'currently in the database, and DELETE ALL TABLES AND ' \
          'SCHEMAS. Are you sure you want to do this?\n\n' \
          'Type "yes" to continue, or "no" to cancel: ' \
          % (db, orm.engine.url))
    else:
      confirm = 'yes'

    if confirm == 'yes':
      # get a list of all schemas used by the app
      default_schema = orm.engine.url.database
      app_schemas = set(orm.Base.metadata._schemas)
      app_schemas.add(default_schema)

      url = deepcopy(orm.engine.url)
      url.database = None
      engine = create_engine(url)
      inspector = inspect(engine)

      # get a list of existing schemas
      db_schemas = set(inspector.get_schema_names())

      schemas = app_schemas.intersection(db_schemas)

      app_tables = set()
      for table in orm.Base.metadata.tables.values():
        schema = table.schema or default_schema
        app_tables.add('%s.%s' % (schema, table.name))

      metadata = MetaData()
      db_tables = []
      all_fks = []

      for schema in schemas:
        for table_name in inspector.get_table_names(schema):
          fullname = '%s.%s' % (schema, table_name)
          if fullname not in app_tables:
            continue
          fks = []
          for fk in inspector.get_foreign_keys(table_name, schema=schema):
            if not fk['name']:
                continue
            fks.append(ForeignKeyConstraint((),(),name=fk['name']))
          t = Table(table_name, metadata, *fks, schema=schema)
          db_tables.append(t)
          all_fks.extend(fks)

      session = Session(bind=engine)
      for fkc in all_fks:
        session.execute(DropConstraint(fkc))
      for table in db_tables:
        session.execute(DropTable(table))
      for schema in schemas:
        session.execute(DropSchema(schema))
      session.commit()
      session.bind.dispose()

    else:
      self.stdout.write("Purge cancelled.\n")
