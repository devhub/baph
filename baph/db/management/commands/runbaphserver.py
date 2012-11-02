from django.core.management.commands.runserver import BaseRunserverCommand

class Command(BaseRunserverCommand):
    def validate(self, app=None, display_num_errors=False):
        pass
