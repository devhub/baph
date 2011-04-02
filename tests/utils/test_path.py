# -*- coding: utf-8 -*-

from baph.test.base import TestCase
from baph.utils.path import relpath
import os
import posixpath


class PathTestClass(TestCase):
    '''Tests :mod:`baph.utils.path`.'''

    def test_relpath(self):
        '''Copied from Python SVN python/trunk/Lib/test/test_posixpath.py,
        revision 78735.
        '''
        (real_getcwd, os.getcwd) = (os.getcwd, lambda: r'/home/user/bar')
        try:
            curdir = os.path.split(os.getcwd())[-1]
            self.assertRaises(ValueError, relpath, '')
            self.assertEqual(relpath('a'), 'a')
            self.assertEqual(relpath(posixpath.abspath('a')), 'a')
            self.assertEqual(relpath('a/b'), 'a/b')
            self.assertEqual(relpath('../a/b'), '../a/b')
            self.assertEqual(relpath('a', '../b'), '../%s/a' % curdir)
            self.assertEqual(relpath('a/b', '../c'), '../%s/a/b' % curdir)
            self.assertEqual(relpath('a', 'b/c'), '../../a')
            self.assertEqual(relpath('a', 'a'), '.')
        finally:
            os.getcwd = real_getcwd
