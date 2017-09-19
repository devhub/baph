import os

from .loader import PreconfigLoader


def preconfigure():
  preconfig = PreconfigLoader.load()
  if preconfig:
    preconfig.populate_env()
