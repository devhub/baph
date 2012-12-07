from baph.utils.importing import import_any_module
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Runs this project as a FastCGI application. Requires flup."
    args = '[various KEY=val options, use `runfcgi help` for help]'

    def handle(self, *args, **options):
        from django.conf import settings
        from django.utils import translation
        # Activate the current language, because it won't get activated later.
        try:
            translation.activate(settings.LANGUAGE_CODE)
        except AttributeError:
            pass
        from django.core.servers.fastcgi import runfastcgi
        runfastcgi(args)
        
    def usage(self, subcommand):
        from django.core.servers.fastcgi import FASTCGI_HELP
        return FASTCGI_HELP
        
    def validate(self, app=None, display_num_errors=False):
        from django.conf import settings
        for app in settings.INSTALLED_APPS:
            print 'installing models from %s' % app
            import_any_module(['%s.models' % app], raise_error=False)
