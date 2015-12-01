from django.dispatch import Signal


add_timing = Signal(providing_args=['key', 'time'])