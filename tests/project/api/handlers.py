# -*- coding: utf-8 -*-

from piston.handler import BaseHandler


class HelloHandler(BaseHandler):

    def read(self, request):
        return {
            'result': 'world',
        }
