from __future__ import absolute_import
from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.ext.associationproxy import association_proxy

from baph.auth.models.permission.utils import get_or_fail
from baph.db import ORM
from baph.db.types import Dict


orm = ORM.get()
Base = orm.Base


def create_usergroup(user):
    from baph.auth.models import UserGroup
    return UserGroup(user=user)


class AbstractBaseGroup(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    context = Column(Dict)

    users = association_proxy('user_groups', 'user', creator=create_usergroup)
    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename',
                                  creator=get_or_fail)


class BaseGroup(AbstractBaseGroup):
    __tablename__ = 'baph_auth_groups'
    __requires_subclass__ = True
    name = Column(Unicode(100))
