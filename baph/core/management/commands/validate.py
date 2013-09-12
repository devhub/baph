from sqlalchemy.orm import configure_mappers

from baph.core.management.base import NoArgsCommand
from baph.db.orm import Base
from baph.forms.models import fields_for_model
import sys

class Command(NoArgsCommand):
    help = "Validates all installed models."

    # we'll do this manually below
    requires_model_validation = False

    def handle_noargs(self, **options):
        self.validate(display_num_errors=True)
        #configure_mappers()
        
        print '\nPost-Validation Tables:'
        for table in Base.metadata.tables:
            print '\t', table
        """
        print '\nPost-Validation Class Registry:'
        for k,v in sorted(Base._decl_class_registry.items()):
            print '\t', k, v
            if not hasattr(v, '__mapper__'):
                continue
            print fields_for_model(v)
            
            #for desc in v.__mapper__.all_orm_descriptors:
            #    print '\t  -', desc, type(desc)
        """
        """            
        print '\nTable Data:'
        for table in Base.metadata.sorted_tables:
            print '\t', table
            for col in table.columns:
                print '\t\t', col
        """
