#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name='baph',
      version='0.2.1',
      install_requires=[
          'Coffin',
          'Django >= 1.2',
          'SQLAlchemy < 0.5.999',
      ],
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
