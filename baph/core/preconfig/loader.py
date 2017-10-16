import imp
import inspect
import os
from pkg_resources import get_distribution
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
    if root is None and 'BAPH_APP' in os.environ:
      app = os.environ['BAPH_APP']
      dist = get_distribution(app)
      root = os.path.join(dist.location, app)
      '''
      try:
        _, root, _ = imp.find_module(app, sys.path)
      except:
        pass
      '''

    if root is None:
      path = os.path.realpath(sys.argv[0])
      root = os.path.dirname(path)

    if root not in cls.cache:
      profile = load_preconfig_profile(root)
      if not profile:
        return None
      cls.cache[root] = Preconfiguration(root, profile)
    return cls.cache[root]

