from __future__ import absolute_import
from django.conf import settings
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship

from baph.auth.models.group import Group
from baph.auth.models.permission import Permission
from baph.auth.models.user import User
from baph.db import ORM


orm = ORM.get()
Base = orm.Base

PERMISSION_TABLE = getattr(settings, 'BAPH_PERMISSION_TABLE',
                           'baph_auth_permissions')


class PermissionAssociation(Base):
    __tablename__ = PERMISSION_TABLE + '_assoc'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    group_id = Column(Integer, ForeignKey(Group.id))
    perm_id = Column(Integer, ForeignKey(Permission.id), nullable=False)

    user = relationship(
        User,
        backref=backref('permission_assocs',
                        cascade='all, delete-orphan'))
    group = relationship(
        Group,
        backref=backref('permission_assocs',
                        cascade='all, delete-orphan'))
    permission = relationship(Permission, lazy='joined')

    codename = association_proxy('permission', 'codename')
