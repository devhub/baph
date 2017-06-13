#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

setup(name='baph',
      version='0.3.37',
      install_requires=[
          'Coffin >= 0.3.8',
          'Django >= 1.6',
          'SQLAlchemy >= 0.9.4',
      ],
      include_package_data=True,
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
