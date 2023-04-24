from __future__ import absolute_import
from django.dispatch import Signal


add_timing = Signal(providing_args=['key', 'time'])