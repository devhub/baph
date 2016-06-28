import functools


class memoize(object):
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __get__(self, instance, type=None):
        if instance is None:
            return self.func
        return functools.partial(self, instance)

    def __call__(self, *args, **kwargs):
        instance = args[0]
        key = (self.func, type(instance), args[1:], frozenset(kwargs.items()))
        try:
            res = self.cache[key]
        except KeyError:
            res = self.cache[key] = self.func(*args, **kwargs)
        return res

class cachedclassproperty(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        res = self.func(cls)
        setattr(cls, self.func.__name__, res)
        return res