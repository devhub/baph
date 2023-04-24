# -*- coding: utf-8 -*-

from __future__ import absolute_import
from baph.utils.importing import import_attr
import os

__all__ = ['relpath']

relpath = import_attr(['os.path'], 'relpath', raise_error=False)
if not relpath:
    # Adapted from http://jimmyg.org/work/code/barenecessities/
    # License: MIT

    def relpath(path, start=os.path.curdir):
        '''Return a relative version of a path'''
        if not path:
            raise ValueError('no path specified')
        start_list = os.path.abspath(start).split(os.path.sep)
        path_list = os.path.abspath(path).split(os.path.sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))
        rel_list = [os.path.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return os.path.curdir
        return os.path.join(*rel_list)
