import functools


class memoize(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, type=None):
        if instance is None:
            return self.func
        return functools.partial(self, instance)

    def __call__(self, *args, **kw):
        instance = args[0]
        key = (self.func.__name__, args[1:], frozenset(kw.items()))
        try:
            res = instance.__dict__[key]
        except KeyError:
            res = instance.__dict__[key] = self.func(*args, **kw)
        return res
