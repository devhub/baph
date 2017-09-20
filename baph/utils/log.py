import logging

from django.utils.log import DEFAULT_LOGGING

from baph.utils.module_loading import import_string


def configure_logging(logging_config, logging_settings):
  if logging_config:
    # First find the logging configuration function ...
    logging_config_func = import_string(logging_config)

    logging.config.dictConfig(DEFAULT_LOGGING)

    # ... then invoke it with the logging settings
    if logging_settings:
      logging_config_func(logging_settings)