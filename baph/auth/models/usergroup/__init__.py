from sqlalchemy import (Boolean, Column, ForeignKey, Index, Integer,
                        PrimaryKeyConstraint, String)
from sqlalchemy.orm import backref, relationship

from baph.auth.models.group import Group
from baph.auth.models.user import User
from baph.db import ORM


orm = ORM.get()
Base = orm.Base


class UserGroup(Base):
    '''User groups'''
    __tablename__ = 'baph_auth_user_groups'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'group_id', 'key', 'value'),
        Index('idx_group_context', 'group_id', 'key', 'value'),
        Index('idx_context', 'key', 'value'),
        )

    class Meta:
        permission_parents = ['user']
        permission_handler = 'user'

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    group_id = Column(Integer, ForeignKey(Group.id), nullable=False)
    key = Column(String(32), default='')
    value = Column(String(32), default='')
    deny = Column(Boolean, default=False)

    user = relationship(
        User, backref=backref('groups',
                              cascade='all, delete-orphan'))
    group = relationship(
        Group,
        backref=backref('user_groups',
                        cascade='all, delete-orphan'))
