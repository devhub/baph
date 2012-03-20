#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name='baph',
      version='0.2.2',
      install_requires=[
          'Coffin',
          'Django >= 1.2',
          'SQLAlchemy < 0.7.5',
      ],
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
