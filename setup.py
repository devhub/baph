#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name='baph',
      version='0.2.11',
      install_requires=[
          'Coffin',
          'Django >= 1.3',
          'SQLAlchemy >= 0.8.0',
      ],
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
