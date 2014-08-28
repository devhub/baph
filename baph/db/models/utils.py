import types

from sqlalchemy.ext.declarative.clsregistry import _class_resolver


def has_inherited_table(cls):
    """Given a class, return True if any of the classes it inherits from has a
    mapped table, otherwise return False.
    """
    for class_ in cls.__mro__:
        if cls == class_:
            continue
        if getattr(class_, '__table__', None) is not None:
            return True
    return False

def class_resolver(cls):
    """
    Takes a class, string, or lazy resolver and returns the
    appropriate SQLA class
    """
    from baph.db.orm import Base
    if isinstance(cls, basestring):
        # string reference
        cls = Base._decl_class_registry[cls]
    if isinstance(cls, types.FunctionType):
        # lazy-loaded Model
        cls = cls()
    if isinstance(cls, _class_resolver):
        # lazy-loaded Model
        cls = cls()
    if hasattr(cls, 'is_mapper') and cls.is_mapper:
        # we found a mapper, grab the class from it
        cls = cls.class_
    if issubclass(cls, Base):
        # sqla class
        return cls
    raise Exception('could not resolve class: %s' % cls)
