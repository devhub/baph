from types import FunctionType

from django.conf import settings


USER_ORG_KEY = getattr(settings, 'BAPH_USER_ORG_KEY')
USER_ORG_REL = getattr(settings, 'BAPH_USER_ORG_RELATION')
GROUP_ORG_KEY = getattr(settings, 'BAPH_GROUP_ORG_KEY')
GROUP_ORG_REL = getattr(settings, 'BAPH_GROUP_ORG_RELATION')


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
        ctx = self.get_context()
        permissions = {}
        for user_group in self.groups:
            if user_group.key:
                ctx[user_group.key] = user_group.value
            group = user_group.group
            org_id = getattr(group, GROUP_ORG_KEY)
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

        # TODO: this will have a better solution soon
        org_cls = getattr(type(self), USER_ORG_REL).property.argument
        if isinstance(org_cls, FunctionType):
            org_cls = org_cls()
        current_org_id = org_cls.get_current_id()
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

