import copy

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.collections import MappedCollection
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import identity_key

from baph.db.orm import ORM


orm = ORM.get()
Base = orm.Base

def clone_obj(obj, user, rules={}, registry={}, path=None, root=None,
              cast_to=None):
    """Clones an object and returns the clone.

    Default behavior is to only process columns (no relations), and
    to skip any columns which are primary keys or foreign keys.
    
    :param obj: the sqlalchemy instance to clone
    
    :param user: the user object to be used to populate fields given in
        the 'chown' directive. relations will be populated with user,
        and columns will be populated with user.id
        
    :param rules: a dictionary of rules, associating each 'path' with a
        series of directives which provide information on how to handle
        the fields present on the instance. More info later.
        
    :param registry: a mapping of class/pk comblinations linked to the
        cloned instances which were generated from those keys. This field
        should never be initialized by the user, and is used only to pass
        the updated registry to recursive calls to clone_obj
        
    :param path: the path to be used when looking up the rules for the
        current object. This is an internally used field, and users should
        not ever need to provide a value here.
        
    :param root: the top-level object. This is set automatically, and users
        should not need to use this field
    
    Rule dictionaries can contain the following directives:
    
    :callback: contains a function to be called on the cloned object after
        all properties have been processed. The given function must take 3
        args (active instance, active user, root object) and return the
        modified instance.

    :chown: (columns & relations) contains a list of properties to be
        populated with the provided 'user' param. Columns will be populated
        with user.id, while relations will receive the user object.

    :excludes: (columns) contains a list of properties to skip when processing
        the columns on the object. relations are ignored unless explcitly
        specified, so adding a relation property here isn't necessary. primary
        and foreign keys are also skipped by default.

    :preserve: (columns & relations) contains a list of properties to be
        copied EXACTLY during the cloning process. This can be used to
        create references to existing global objects which should not
        be cloned, such as foreign keys to a master 'category' list, etc.
        
    :relations: (relations) contains a list of properties which should be
        cloned along with the parent. When drilling down to process a relation,
        the relation name is added to the current 'path' value, and the new
        path is used to look up the rules for processing the related objects.

    :relinks: (relations) contains a list of properties to be 'relinked' during
        the cloning process. During a relink, the registry is first checked, to
        see if the target object was already cloned earlier in the cloning 
        process, and if found, that object will be used instead of creating a
        new one.
    """
    cls, pk = identity_key(instance=obj)
    if not path:
        # we need to force a complete reload to ensure all polymorphic 
        # relations are using their subclasses, and not the base class
        session = object_session(obj)
        session.expunge_all()
        session.close()
        session = orm.sessionmaker()
        obj = session.query(cls).get(pk)

    if not rules and not hasattr(cls, '__cloning_rules__'):
        raise Exception('Class %s cannot be cloned' % cls)
    rules = copy.deepcopy(rules or cls.__cloning_rules__)
    cls_mapper = class_mapper(obj.__class__)
    if cast_to:
        instance = cast_to()
        # we don't want the old discriminator to overwrite the 
        # one auto-populated by creation of the subclass
        discriminator = cls.__mapper_args__['polymorphic_on']
        rules['Site']['excludes'].append(discriminator)
    else:
        instance = obj.__class__()
    if not cls in registry:
        registry[cls] = {}
    registry[cls][pk] = instance
    if not path:
        path = cls.__name__
    if not root:
        root = instance

    local_rules = rules.get(path, {})
    chown = local_rules.get('chown', [])
    relations = local_rules.get('relations', [])
    excludes = local_rules.get('excludes', [])
    relinks = local_rules.get('relinks', [])
    preserve = local_rules.get('preserve', [])
    callback = local_rules.get('callback', None)

    " first, copy over all preserved values "
    for key in preserve:
        " this value will be carried over regardless, useful for "
        " handling fks or relationships to fixed objects which "
        " should not have copies created. We do this first so we "
        " can handle association proxies, which won't show up in "
        " iterate_properties "
        setattr(instance, key, getattr(obj, key))
        continue
        
    " next, copy over column properties, skipping the props in 'excludes' "
    for prop in cls_mapper.iterate_properties:
        if prop.key in preserve:
            " we just handled this "
            continue
        if prop.key in chown:
            " this value will be replaced with the new owner "
            if isinstance(prop, ColumnProperty):
                setattr(instance, prop.key, user.id)
            elif isinstance(prop, RelationshipProperty):
                setattr(instance, prop.key, user)
            else:
                raise Exception('cannot chown field of type %s'
                    % type(prop))
            continue
        if not isinstance(prop, ColumnProperty):
            " relations are not processed automatically, to prevent "
            " infinite loops caused by backrefs, and to allow them "
            " to be processed in a specific order if necessary "
            continue
        if prop.key in excludes:
            continue
        cols = prop.columns
        if any(cols[i].foreign_keys for i in range(0, len(cols))):
            " an associated column has foreign keys- skip it "
            " to carry over a foreign key during the cloning process, "
            " add it to 'preserve' "
            continue
        if any(cols[i].primary_key for i in range(0, len(cols))):
            " not possible to carry over a primary key "
            continue
        setattr(instance, prop.key, getattr(obj, prop.key))

    " next, process any specified relations in the given order "
    for key in relations:
        try:
            prop = cls_mapper.get_property(key)
        except: # prop not found, possibly a polymorphic prop missing on base
            continue

        if not isinstance(prop, RelationshipProperty):
            raise ValueError('"relations" must contain only relationships')

        value = getattr(obj, key)
        path_ = '.'.join((path, key))

        if not value:
            setattr(instance, key, value)
        elif isinstance(value, MappedCollection):
            new_map = {}
            for name,item in value.items():
                new_map[name] = clone_obj(item, user, rules, registry, path_,
                    root)
            setattr(instance, key, new_map)
        elif isinstance(value, list): # onetomany or manytomany
            setattr(instance, key, [clone_obj(item, user, rules, registry,
                path_, root) for item in value])
        else: # onetoone or manytoone
            setattr(instance, key, clone_obj(value, user, rules, registry,
                path_, root))
    
    " now try using the registry to relink any relationships "
    " which link to cloned items that have been generated already "
    for key in relinks:
        try:
            prop = cls_mapper.get_property(key)
        except: # prop not found, possibly a polymorphic prop missing on base
            continue

        if not isinstance(prop, RelationshipProperty):
            raise ValueError('"relinks" must contain only relationships')
        value = getattr(obj, key)
        path_ = '.'.join((path, key))

        if not value:
            setattr(instance, key, value)
        elif isinstance(value, list): # onetomany or manytomany
            objs = []
            for item in value:
                cls_, pk_ = identity_key(instance=item)
                if not cls_ in registry:
                    raise ValueError('Class %s isn\'t present in the registry'
                        % cls_)
                try:
                    objs.append(registry[cls_][pk_])
                except:
                    objs.append(clone_obj(item, user, rules, registry, path_, root))
                    #raise ValueError('Object of class %s with pk %s was not '
                    #    'found in the registry' % (cls_, pk_))
            setattr(instance, key, objs)
        else: # onetoone or manytoone
            cls_, pk_ = identity_key(instance=value)
            if not cls_ in registry:
                raise ValueError('Class %s isn\'t present in the registry'
                    % cls_)
            try:
                setattr(instance, key, registry[cls_][pk_])
            except:
                setattr(instance, key, 
                    clone_obj(value, user, rules, registry, path_, root))
                #raise ValueError('Object of class %s with pk %s was not '
                #    'found in the registry' % (cls_, pk_))

    if callback:
        instance = callback(instance, user, root)
    
    return instance
    
def full_instance_dict(obj, rules={}, path=None):
    if path is None:
        path = obj.__class__.__mapper__.base_mapper.class_.__name__
    if not rules and not hasattr(obj, '__cloning_rules__'):
        raise Exception('object %s cannot be serialized' % obj)
    rules = rules or obj.__cloning_rules__

    local_rules = rules.get(path, {})
    data = {}
    for prop in class_mapper(obj.__class__).iterate_properties:
        if isinstance(prop, ColumnProperty):
            data[prop.key] = getattr(obj, prop.key)
        elif isinstance(prop, RelationshipProperty):
            if not prop.key in local_rules.get('relations', []):
                continue
            rel_path = '.'.join([path,prop.key])
            v = getattr(obj, prop.key)

            if isinstance(v, Base):
                val = full_instance_dict(v, rules, rel_path)
            elif isinstance(v, list):
                val = []
                for i in v:
                    if isinstance(i, Base):
                        val.append(full_instance_dict(i, rules, rel_path))
                    else:
                        val.append(i)
            elif isinstance(v, dict):
                # collection_class = MappedCollection
                val = {}
                for i,k in v.items():
                    if isinstance(k, Base):
                        val[i] = full_instance_dict(k, rules, rel_path)
                    else:
                        val[i] = k
            else:
                val = v
            data[prop.key] = val
        continue
    return data
