import json
import logging

from django.conf import settings
from sqlalchemy import *
from sqlalchemy import inspect
from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.orm import lazyload

from baph.db import ORM
from baph.db.models.loading import cache
from baph.db.models.utils import class_resolver, column_to_attr, key_to_value


logger = logging.getLogger('authorization')

def convert_filter(k, cls=None):
    """Convert a string filter into a column-based filter"""
    if not isinstance(k, basestring):
        raise Exception('convert_filters keys must be strings')
    frags = k.split('.')
    attr = frags.pop()
    joins = []
    if not frags:
        # only attr provided, use current model
        if not cls:
            raise Exception('convert_filter: cls is required for '
                'single-dotted keys')
        model = cls
    else:
        # dotted format, chained relations
        model = string_to_model(frags.pop(0))
        for frag in frags:
            model = model.get_related_class(frag)
    
    col = getattr(model, attr)
    return (col, joins)

def string_to_model(string):
    from baph.db.orm import Base
    if string in Base._decl_class_registry:
        return Base._decl_class_registry[string]
    elif string.title() in Base._decl_class_registry:
        return Base._decl_class_registry[string.title()]
    else:
        # this string doesn't match a resource
        return None

class PermissionStruct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)
        self._explicit = False
        self._deny = False

    @property
    def opcode(self):
        if str(self.value).startswith('['):
            return 'in'
        else:
            return 'eq'

class UserPermissionMixin(object):

    def get_user_permissions(self):
        ctx = self.get_context()
        permissions = {}
        for assoc in self.permission_assocs:
            perm = assoc.permission
            model_name = perm.resource
            if model_name not in permissions:
                permissions[model_name] = {}
            if perm.action not in permissions[model_name]:
                permissions[model_name][perm.action] = set()
            perm = PermissionStruct(**perm.to_dict())
            if perm.value:
                perm.value = perm.value % ctx
            permissions[model_name][perm.action].add(perm)
        return permissions

    def get_group_permissions(self):
        from baph.auth.models import Organization
        ctx = self.get_context()
        permissions = {}
        for user_group in self.groups:
            context = ctx.copy()
            # if the group association has additional context, add it
            if user_group.key:
                context[user_group.key] = user_group.value
            group = user_group.group
            # if the group has additional context, add it
            if group.context:
                context.update(group.context)

            org_id = str(getattr(group, Organization._meta.model_name+'_id'))
            if org_id not in permissions:
                permissions[org_id] = {}
            perms = permissions[org_id]
            for assoc in group.permission_assocs:
                perm = assoc.permission
                model_name = perm.resource
                if model_name not in perms:
                    perms[model_name] = {}
                if perm.action not in perms[model_name]:
                    perms[model_name][perm.action] = set()
                perm = PermissionStruct(**perm.to_dict())
                if user_group.key:
                    perm._explicit = True
                if user_group.deny:
                    perm._deny = True
                
                if perm.value:
                    try:
                        perm.value = perm.value % context
                    except KeyError as e:
                        raise Exception('Key %s not found in permission '
                            'context. If this is a single-value permission, '
                            'ensure the key and value are present on the '
                            'UserGroup association object.' % str(e))
                perms[model_name][perm.action].add(perm)
        return permissions

    def get_all_permissions(self):
        permissions = self.get_group_permissions()
        user_perms = self.get_user_permissions()
        if not user_perms:
            return permissions
        if not None in permissions:
            permissions[None] = {}
        for resource, actions in user_perms.items():
            if resource not in permissions[None]:
                permissions[None][resource] = {}
            for action, perms in actions.items():
                if action not in permissions[None][resource]:
                    permissions[None][resource][action] = set()
                permissions[None][resource][action].update(perms)
        return permissions

    def get_current_permissions(self):
        if hasattr(self, '_perm_cache'):
            return self._perm_cache
        from baph.auth.models import Organization
        current_org_id = str(Organization.get_current_id())
        perms = {}
        for org_id, org_perms in self.get_all_permissions().items():
            if not org_id in (None, current_org_id):
                continue
            for rsrc, rsrc_perms in org_perms.items():
                if not rsrc in perms:
                    perms[rsrc] = {}
                for action, action_perms in rsrc_perms.items():
                    if not action in perms[rsrc]:
                        perms[rsrc][action] = set()
                    perms[rsrc][action].update(action_perms)
        setattr(self, '_perm_cache', perms)
        return perms

    def get_resource_permissions(self, resource, action=None):
        if not resource:
            raise Exception('resource is required for permission filtering')
        perms = self.get_current_permissions()
        if resource not in perms:
            return set()
        perms = perms.get(resource, {})
        if action:
            perms = perms.get(action, {})
        return perms

    def has_resource_perm(self, resource):
        if not self.is_authenticated():
            # user is not logged in
            return False
        perms = self.get_resource_permissions(resource)
        return bool(perms)

    def has_perm(self, resource, action, filters=None):
        logger.debug('has_perm %s:%s called for user %s' 
            % (action, resource, self.id))
        logger.debug('filters: %s' % filters)
        if not filters:
            filters = {}
        ctx = self.get_context()
        logger.debug('perm context: %s' % ctx)
        from baph.db.orm import ORM
        if not self.is_authenticated():
            # user is not logged in
            return False

        perms = self.get_resource_permissions(resource, action)
        if not perms:
            # user has no applicable permissions
            return False
        for p in perms:
            logger.debug('  perm: %s' % p)

        orm = ORM.get()
        cls_name = tuple(perms)[0].resource
        cls = orm.Base._decl_class_registry[cls_name]

        requires_load = False
        if action == 'add':
            # add operations have no pk info, so we can't load from db
            pass            
        else:
            # if we have all 'protected' fks, we can evaluate without a
            # load. otherwise, we need to load to validate
            for rel in cls._meta.permission_parents:
                fk = tuple(getattr(cls, rel).property.local_columns)[0].name
                if not any (key in filters for key in (rel, fk)):
                    requires_load = True
        
        session = orm.sessionmaker()

        if requires_load:
            obj = session.query(cls).filter_by(**filters).first()
        else:
            obj = cls(**filters)
            if obj in session:
                session.expunge(obj)
        return self.has_obj_perm(resource, action, obj)

    def has_obj_perm(self, resource, action, obj):
        logger.debug('\nhas_obj_perm "%s %s" called for user %s'
            % (action, resource, self.id))
        logger.debug('  obj: %s' % obj)
        # TODO: auto-generate resource by checking base_mapper of polymorphics
        if type(obj)._meta.permission_handler:
            # permissions for this object are based off parent object
            parent_obj = obj.get_parent(type(obj)._meta.permission_handler)
            if not parent_obj:
                # nothing to check perms against, assume True
                return True
            parent_res = type(parent_obj).resource_name
            if action != 'view':
                action = 'edit'

            return self.has_obj_perm(parent_res, action, parent_obj)

        ctx = self.get_context()
        logger.debug('perm context: %s' % ctx)

        perms = self.get_resource_permissions(resource, action)
        if not perms:
            # user has no valid permissions for this resource/action pair
            logger.debug('user has no valid permissions')
            return False

        for p in perms:
            logger.debug('  perm: %s' % p.codename)

        perm_map = {}
        explicit = []
        matches = []
        for p in perms:
            if not p.key:
                # this is a boolean permission (not a key/value filter)
                if p._deny:
                    return False
                matches.append(p)
                continue
            if p._explicit:
                explicit.append(p.key)
            if not (p.key, p._deny) in perm_map:
                perm_map[(p.key, p._deny)] = set()

            if p.opcode == 'in':
                # this is a json-encoded list of values
                values = json.loads(p.value)
            else:
                # this is a single value
                values = [p.value]
            # replace context variables
            values = [str(value) % ctx for value in values]
            perm_map[(p.key, p._deny)].update(values)

        if action == 'add':
            for p in type(obj)._meta.permission_parents:
                attr = getattr(type(obj), p)
                prop = attr.property
                col = prop.local_remote_pairs[0][0]
                col_attr = column_to_attr(type(obj), col)
                if not col_attr.key in perm_map:
                    perm_map[(col_attr.key, False)] = set([None])

        add_errors = []
        for (k, deny), v in perm_map.items():
            logger.debug('testing perm: %s=%s' % (k,v))
            keys = k.split(',')
            key_pieces = [key_to_value(obj, key) for key in keys]

            if key_pieces == [None]:
                value = None
            elif None in key_pieces:
                # this object lacks the values required to form a key
                # so this permission is irrelevant to the current obj
                logger.debug('  object lacks all necessary keys, ignoring perm')
                continue
            else:
                value = ','.join(key_pieces)

            if not value:
                # no value to check
                logger.debug('  object has no value to check')
                continue

            if v == set([None]):
                # no restriction on allowed values
                logger.debug('  object has no restrictions on values')
                continue

            if str(value) in v:
                if action == 'add':
                    if k in explicit:
                        # this perm indicates it can grant access and override
                        # restrictions set by broader permissions. If the key/value
                        # is set on the UserGroup (rather than the permission), the
                        # permission will be 'explicit'
                        logger.debug('match on explicit add permission. deny=%s' % deny)
                        if deny:
                            return False
                        matches.append(v)
                else:
                    # for non-add permissions, a single matching filter will grant
                    # access to the resource
                    logger.debug('match on non-add permission. deny=%s' % deny)
                    if deny:
                        return False
                    matches.append(v)
            else:
                if action == 'add':
                    add_errors.append( (k, value, v) )
                    continue
        if add_errors:
            logger.debug('[INVALID] negative hit on add permission')
            return False

        if action == 'add':
            logger.debug('match on add permission with no disqualifying '
                'criteria. deny=%s' % deny)
            if deny:
                return False
            matches.append(v)

        if matches:
            logger.debug('[VALID] applicable permissions were found')
            return matches
        else:
            logger.debug('[INVALID] %s permission with no qualifying criteria')
            return False

    def get_resource_filters(self, resource, action='view'):
        """
        Returns resource filters in a format appropriate for 
        applying to an existing query
        """
        orm = ORM.get()
        cls = orm.Base._decl_class_registry[resource]
        if cls._meta.permission_handler:
            # permissions for this object are routed to parent object
            parent_cls = cls.get_related_class(cls._meta.permission_handler)
            if action != 'view':
                action = 'edit'
            return self.get_resource_filters(parent_cls.resource_name, action)

        ctx = self.get_context()
        perms = self.get_resource_permissions(resource, action)
        if not perms:
            return False

        allow_filters = []
        deny_filters = []
        for p in perms:
            if not p.key:
                # this is a boolean permission, so cannot be applied as a filter
                continue

            keys = p.key.split(',')
            if p.opcode == 'in':
                # range filter
                values = [json.loads(p.value)]
            else:
                # exact filter
                values = p.value.split(',')

            data = zip(keys, values)
            
            filters = []
            for key, value in data:
                if key in cls._meta.filter_translations:
                    lookup, key = cls._meta.filter_translations[key].split('.',1)
                else:
                    lookup = resource
                cls_ = orm.Base._decl_class_registry[lookup]

                frags = key.split('.')
                attr = frags.pop()
                for frag in frags:
                    cls_ = cls_.get_related_class(frag)

                col = getattr(cls_, attr)
                if p.opcode == 'in':
                    filters.append(col.in_(value))
                else:
                    filters.append(col==value)
            if len(filters) == 1:
                filter_ = filters[0]
            else:
                filter_ = and_(*filters)
            if p._deny:
                deny_filters.append(not_(filter_))
            else:
                allow_filters.append(filter_)

        final_filters = deny_filters[:]
        final_filters.append(or_(*allow_filters))
        return [and_(*final_filters)]