# -*- coding: utf-8 -*-

from __future__ import absolute_import
from piston.handler import BaseHandler


class HelloHandler(BaseHandler):

    def read(self, request):
        return {
            'result': 'world',
        }
