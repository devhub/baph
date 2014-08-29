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
    if hasattr(cls, col.name):
        # the column name is the same as the attr name
        return getattr(cls, col.name)
    for attr_ in inspect(cls).all_orm_descriptors:
        # iterate through descriptors to find one that contains the column
        try:
            assert attr_.property.columns == [col]
            return attr_
        except:
            continue
    return None

def key_to_value(obj, key, raw=False):
    """
    Evaluate chained relations against a target object
    """
    from baph.db.orm import ORM

    frags = key.split('.')
    if not raw:
        col_key = frags.pop()
    current_obj = obj
    
    while frags:
        if not current_obj:
            # we weren't able to follow the chain back, one of the 
            # fks was probably optional, and had no value
            return None
        
        attr_name = frags.pop(0)
        previous_obj = current_obj
        previous_cls = type(previous_obj)
        current_obj = getattr(previous_obj, attr_name)

        if current_obj:
            # proceed to next step of the chain
            continue

        # relation was empty, we'll grab the fk and lookup the
        # object manually
        attr = getattr(previous_cls, attr_name)
        prop = attr.property

        related_cls = class_resolver(prop.argument)
        related_col = prop.local_remote_pairs[0][0]
        attr_ = column_to_attr(previous_cls, related_col)
        related_key = attr_.key
        related_val = getattr(previous_obj, related_key)
        if related_val is None:
            # relation and key are both empty: no parent found
            return None

        orm = ORM.get()
        session = orm.sessionmaker()
        current_obj = session.query(related_cls).get(related_val)

    if raw:
        return current_obj

    value = getattr(current_obj, col_key, None)
    if value:
        return str(value)
    return None

