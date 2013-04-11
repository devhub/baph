import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr


class TimestampMixin(object):

    @declared_attr
    def added(cls):
        return Column(DateTime, default=datetime.datetime.now,
            info={'readonly': True})

    @declared_attr
    def modified(cls):
        return Column(DateTime, default=datetime.datetime.now,
            onupdate=datetime.datetime.now, info={'readonly': True})

