from __future__ import absolute_import
from sqlalchemy import Column, Integer, Unicode

from baph.db import ORM


orm = ORM.get()
Base = orm.Base


class AbstractBaseOrganization(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    @classmethod
    def get_current(cls):
        raise NotImplemented('get_current must be defined on the '
                             'custom Organization model')

    @classmethod
    def get_current_id(cls, request=None):
        org = cls.get_current()
        if not org:
            return None
        if isinstance(org, dict):
            return org['id']
        else:
            return org.id

    @classmethod
    def get_column_key(cls):
        return cls._meta.model_name+'_id'

    @classmethod
    def get_relation_key(cls):
        return cls._meta.model_name


class BaseOrganization(AbstractBaseOrganization):
    __tablename__ = 'baph_auth_organizations'
    __requires_subclass__ = True
    name = Column(Unicode(200), nullable=False)
