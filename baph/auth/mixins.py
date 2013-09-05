from types import FunctionType

from django.conf import settings
from sqlalchemy import *
from sqlalchemy.orm import lazyload


def convert_filter(k, cls=None):
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
            rel = getattr(model, frag)
            joins.append(rel)
            model = rel.property.argument
    if isinstance(model, FunctionType):
        # lazily-loaded class
        model = model()
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

class UserPermissionMixin(object):

    def get_user_permissions(self):
        ctx = self.get_context()
        permissions = {}
        for assoc in self.permission_assocs:
            perm = assoc.permission
            model = string_to_model(perm.resource)
            model_name = model.__name__ if model else perm.resource
            if model_name not in permissions:
                permissions[model_name] = {}
            if perm.action not in permissions[model_name]:
                permissions[model_name][perm.action] = set()
            perm = Struct(**perm.to_dict())
            if perm.value:
                perm.value = perm.value % ctx
            permissions[model_name][perm.action].add(perm)
        return permissions

    def get_group_permissions(self):
        from baph.auth.models import Organization
        ctx = self.get_context()
        permissions = {}
        for user_group in self.groups:
            if user_group.key:
                ctx[user_group.key] = user_group.value
            group = user_group.group
            org_id = getattr(group, Organization._meta.model_name+'_id')
            if org_id not in permissions:
                permissions[org_id] = {}
            perms = permissions[org_id]
            for assoc in group.permission_assocs:
                perm = assoc.permission
                model = string_to_model(perm.resource)
                model_name = model.__name__ if model else perm.resource
                if model_name not in perms:
                    perms[model_name] = {}
                if perm.action not in perms[model_name]:
                    perms[model_name][perm.action] = set()
                perm = PermissionStruct(**perm.to_dict())
                if perm.value:
                    try:
                        perm.value = perm.value % ctx
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
        current_org_id = Organization.get_current_id()
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
        model = string_to_model(resource)
        model_name = model.__name__ if model else resource        
        if model_name not in perms:
            return set()
        perms = perms.get(model_name, {})
        if action:
            perms = perms.get(action, {})
        return perms

    def has_perm(self, resource, action, filters=None):
        from baph.db.orm import ORM
        if not self.is_authenticated():
            # user is not logged in
            return False

        perms = self.get_resource_permissions(resource, action)
        if not perms:
            # user has no applicable permissions
            return False

        for perm in perms:
            if not perm.key:
                # boolean (no filter criteria) permissions are always valid
                return True

        if not filters:
            filters = {}
            # no boolean permissions exist, so filters must be provided in
            # order to determine validity of potential permissions
            raise Exception('has_perm called with no filters, but all ' \
                'located permissions are filter-based')

        model = string_to_model(resource)
        joins = []

        and_filters = []
        for k, v in filters.items():
            col, joins_ = convert_filter(k, model)
            and_filters.append(col == v)
            for j in joins_:
                if not j in joins:
                    joins.append(j)

        or_filters = []
        for perm in perms:
            col, joins_ = convert_filter(perm.key, model)
            or_filters.append(col == perm.value)
            for j in joins_:
                if not j in joins:
                    joins.append(j)

        all_filters = []

        if len(or_filters) > 1:
            all_filters.append(or_(*or_filters))
        elif len(or_filters) == 1:
            all_filters.append(or_filters[0])

        all_filters += and_filters
        if len(all_filters) > 1:
            filters = and_(*all_filters)
        elif len(all_filters) == 1:
            filters = all_filters[0]
        else:
            raise Exception('no filters of any kind found')

        orm = ORM.get()
        session = orm.sessionmaker()
        query = session.query(model) \
            .options(lazyload('*'))

        for join in joins:
            query = query.outerjoin(join)

        query = query.filter(filters) \
            .with_entities(func.count(text('*')))
        return query.scalar() != 0

    def has_resource_perm(self, resource):
        if not self.is_authenticated():
            # user is not logged in
            return False
        
        perms = self.get_resource_permissions(resource)
        return bool(perms)

    def get_resource_filters(self, resource, action='view'):
        """
        Returns resource filters in a format appropriate for 
        applying to an existing query
        """
        from baph.db.orm import Base
        perms = self.get_resource_permissions(resource, action)
        formatted = []

        for p in perms:
            if not p.key:
                # this is a boolean permission, which cannot be applied
                # as a filter
                continue
            model = string_to_model(p.resource)
            keys = p.key.split(',')
            values = p.value.split(',')
            data = zip(keys, values)

            filters = []
            for key, value in data:
                frags = key.split('.')
                cls = Base._decl_class_registry[frags.pop(0)]
                attr = frags.pop()
                for frag in frags:
                    rel = getattr(cls, frag)
                    cls = rel.property.argument
                    if isinstance(cls, FunctionType):
                        # lazy-loaded attr that hasn't been evaluated yet
                        cls = cls()
                col = getattr(cls, attr)
                filters.append(col == value)

            if len(filters) == 1:
                formatted.append(filters[0])
            else:
                formatted.append(and_(*filters))
        return formatted

