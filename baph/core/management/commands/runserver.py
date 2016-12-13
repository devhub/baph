from cStringIO import StringIO

from django.contrib.staticfiles.management.commands.runserver \
    import Command as RunserverCommand

from baph.core.management.validation import get_validation_errors


class Command(RunserverCommand):
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
