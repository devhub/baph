import types

from sqlalchemy import inspect
from sqlalchemy.ext.declarative.clsregistry import _class_resolver


def has_inherited_table(cls):
    # TODO: a fix in sqla 0.9 should make this unnecessary, check it
    """
    Takes a class, return True if any of the classes it inherits from has a
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
    elif isinstance(cls, _class_resolver):
        # lazy-loaded Model
        cls = cls()
    elif hasattr(cls, 'is_mapper') and cls.is_mapper:
        # we found a mapper, grab the class from it
        cls = cls.class_
    if issubclass(cls, Base):
        # sqla class
        return cls
    raise Exception('could not resolve class: %s' % cls)

def column_to_attr(cls, col):
    """
    Takes a class and a column and returns the attribute which 
    references the column
    """
    for attr_ in inspect(cls).all_orm_descriptors:
        try:
            if col in attr_.property.columns:
                return attr_
        except:
            pass    
    return None


