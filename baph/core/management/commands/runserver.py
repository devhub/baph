"""Runserver for Baph.

This is a modified version of the runserver command.
"""

from django.contrib.staticfiles.management.commands import runserver
from django.core.servers.basehttp import WSGIRequestHandler
from django.utils import autoreload

from baph.core.management.new_base import BaseCommand


def get_environ(self):
  for k, v in self.headers.items():
    if '_' in k:
      del self.headers[k]

  environ = super(WSGIRequestHandler, self).get_environ()
  environ['RAW_URI'] = self.path
  return environ

WSGIRequestHandler.get_environ = get_environ


class Command(BaseCommand, runserver.Command):
  def inner_run(self, *args, **kwargs):
    autoreload.raise_last_exception()
    super(BaseCommand, self).inner_run(*args, **kwargs)
