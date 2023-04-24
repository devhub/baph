# -*- coding: utf-8 -*-

from __future__ import absolute_import
from subprocess import PIPE, Popen


def minify(source, output, closure=None, **options):
    '''Minifies JavaScript from a file and outputs it to a different file.
    :type source: :class:`django.core.files.File`
    :type output: :class:`django.core.files.File`
    :param str closure: The absolute path to the Google Closure Compiler
                        JAR file.
    '''
    compiler = ['java', '-jar', closure]
    pipe = Popen(compiler, stdin=PIPE, stdout=PIPE)
    js = pipe.communicate(input=source.read())[0]
    output.write(js)
    output.seek(0)
