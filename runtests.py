#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys
from unittest2 import main

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(current_dir, 'tests')
    sys.path += [current_dir, tests_dir]
    os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
    main(argv=[sys.argv[0]] + ['discover', '-s', tests_dir, '-t',
                               current_dir] + \
              sys.argv[1:])
