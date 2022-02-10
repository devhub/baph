from __future__ import absolute_import
from django.core import validators
import six


class MaxLengthValidator(validators.MaxLengthValidator):
  def clean(self, content):
    if isinstance(content, six.text_type):
      return len(content.encode('utf8'))
    else:
      return len(content)
