from .base import BaseOrganization


class Organization(BaseOrganization):
    class Meta:
        swappable = 'BAPH_ORGANIZATION_MODEL'
