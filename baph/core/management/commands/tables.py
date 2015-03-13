from baph.db.orm import ORM
from django.core.management.base import BaseCommand


orm = ORM.get()
Base = orm.Base
engine = orm.engine
default_schema = engine.url.database

class Command(BaseCommand):

    def handle(self, *args, **options):
        tables = [(table.schema or default_schema, table.name)
            for table in Base.metadata.tables.values()]
        for table in sorted(tables):
            print '.'.join(table)

