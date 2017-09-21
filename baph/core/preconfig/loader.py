import imp
import inspect
import os
import sys

from .config import Preconfiguration
from .utils import load_preconfig_profile


PRECONFIG_MODULE_NAME = 'preconfig'
CONFIG_FOLDERS = ('', 'config', 'conf')

class PreconfigLoader(object):
  cache = {}

  def __init__(self):
    raise Exception('PreconfigLoader is not initializable')

  @classmethod
  def load(cls, root=None):
    if root is None:
      path = os.path.realpath(sys.argv[0])
      root = os.path.dirname(path)
    if root not in cls.cache:
      profile = load_preconfig_profile(root)
      if not profile:
        return None
      cls.cache[root] = Preconfiguration(root, profile)
    return cls.cache[root]

