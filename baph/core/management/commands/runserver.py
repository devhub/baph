from cStringIO import StringIO
import sys

from django.conf import settings
from django.core.management.commands.runserver import Command as Command_

from baph.core.management.base import handle_default_options, OutputWrapper
from baph.core.management.validation import get_validation_errors
from baph.utils.importing import import_any_module


class Command(Command_):
    def validate(self, app=None, display_num_errors=False):
        s = StringIO()
        num_errors = get_validation_errors(s, app)
        if num_errors:
            s.seek(0)
            error_text = s.read()
            raise CommandError("One or more models did not validate:\n%s" % error_text)
        if display_num_errors:
            self.stdout.write("%s error%s found\n" 
                % (num_errors, num_errors != 1 and 's' or ''))
