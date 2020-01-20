from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import RelationshipProperty

from baph.auth.models.organization import Organization
from .base import BaseGroup


class Group(BaseGroup):
    class Meta:
        swappable = 'BAPH_GROUP_MODEL'


col_key = Organization._meta.model_name + '_id'
col = getattr(BaseGroup.__table__.c, col_key, None)
if col is None:
    setattr(BaseGroup, col_key,
            Column(Integer, ForeignKey(Organization.id), index=True))

rel_key = Organization._meta.model_name
rel = getattr(Group, rel_key, None)
if rel is None:
    rel = RelationshipProperty(Organization,
                               backref=Group._meta.model_name_plural,
                               foreign_keys=[getattr(BaseGroup, col_key)])
    setattr(Group, rel_key, rel)
