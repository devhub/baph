from django.conf import settings
from sqlalchemy import Column, Integer, String, Unicode

from baph.db import ORM


orm = ORM.get()
Base = orm.Base

PERMISSION_TABLE = getattr(settings, 'BAPH_PERMISSION_TABLE',
                           'baph_auth_permissions')


class Permission(Base):
    __tablename__ = PERMISSION_TABLE
    __table_args__ = {
        'info': {'preserve_during_flush': True},
        }
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))
    codename = Column(String(100), unique=True)
    resource = Column(String(50))
    action = Column(String(16))
    key = Column(String(100))
    value = Column(String(50))
