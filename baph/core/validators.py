from django.core import validators


class MaxLengthValidator(validators.MaxLengthValidator):
  def clean(self, content):
    if isinstance(content, unicode):
      return len(content.encode('utf8'))
    else:
      return len(content)
