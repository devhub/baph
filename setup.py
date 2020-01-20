#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

setup(name='baph',
      version='0.3.4',
      install_requires=[
          'Coffin',
          'Django >= 1.5',
          'funcy',
          'SQLAlchemy >= 0.9.0',
          'python-dotenv == 0.7.1',
          'functools32 == 3.2.3.post2',
          'chainmap == 1.0.2',
      ],
      include_package_data=True,
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
