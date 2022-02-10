from __future__ import absolute_import
import random
import string
import time
from six.moves import range


def random_string(size=16, chars=None):
    if chars is None:
        chars = []
        chars.extend([i for i in string.ascii_letters])
        chars.extend([i for i in string.digits])
    s = ''
    for i in range(size):
        s += chars[random.randint(0, len(chars) - 1)]
        random.seed = int(time.time())
        random.shuffle(chars)
    return s
