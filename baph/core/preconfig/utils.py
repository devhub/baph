from __future__ import absolute_import
import imp
import os


PRECONFIG_MODULE_NAME = 'preconfig'
CONFIG_FOLDERS = ('', 'config', 'conf')

def join_non_empty(delimiter, *args):
  return delimiter.join([x for x in args if x])

def load_preconfig_module(root):
  folders = [os.path.join(root, folder) for folder in CONFIG_FOLDERS]
  try:
    modinfo = imp.find_module(PRECONFIG_MODULE_NAME, folders)
    return imp.load_module(PRECONFIG_MODULE_NAME, *modinfo)
  except:
    return None

def load_preconfig_profile(root):
  module = load_preconfig_module(root)
  if not module:
    return None
  return {k: v for k,v in module.__dict__.items()
          if k.startswith('PRECONFIG_')}

def with_empty(values):
  if '' in values:
    return values
  return [''] + values
