

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
