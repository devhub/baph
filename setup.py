#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name='baph',
      version='0.3.2',
      install_requires=[
          'Coffin',
          'Django >= 1.5',
          'SQLAlchemy >= 0.9.0',
      ],
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
