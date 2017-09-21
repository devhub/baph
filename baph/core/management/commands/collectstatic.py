from django.contrib.staticfiles.management.commands import collectstatic

from baph.core.management.new_base import BaseCommand


class Command(BaseCommand, collectstatic.Command):
  pass
