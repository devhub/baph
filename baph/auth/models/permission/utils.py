from __future__ import absolute_import
import funcy as f

from baph.auth.models.permission import Permission
from baph.db import ORM


orm = ORM.get()


@f.make_lookuper
def get_perm_id():
    " return the id corresponding to a given codename "
    session = orm.sessionmaker()
    return session.query(Permission.codename, Permission.id).all()


def get_or_fail(codename):
    from baph.auth.models.permissionassociation import PermissionAssociation
    try:
        perm_id = get_perm_id(codename)
        return PermissionAssociation(perm_id=perm_id)
    except KeyError:
        raise ValueError('%s is not a valid permission codename' % codename)
