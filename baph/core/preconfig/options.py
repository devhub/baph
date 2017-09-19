


class BaseOption(object):
  def __init__(self, name, args, default=None, choices=None, required=False):
    self.name = name
    self.args = args
    self.default = default
    self.choices = choices
    self.required = required

  @property
  def metavar(self):
    return self.name.upper()

  @property
  def arg_params(self):
    args = self.args
    kwargs = {
      'metavar': self.metavar,
      'dest': self.name,
      'default': self.default,
      'choices': self.choices,
      'required': self.required,
    }
    return (args, kwargs)

  def add_to_parser(self, parser):
    args, kwargs = self.arg_params
    parser.add_argument(*args, **kwargs)

class ModuleOption(BaseOption):
  def __init__(self, order=None, **kwargs):
    super(ModuleOption, self).__init__(**kwargs)
    self.order = order or self.name

class PackageOption(BaseOption):
  def __init__(self, base='settings', prefix=None, **kwargs):
    super(PackageOption, self).__init__(**kwargs)
    self.base = base
    self.prefix = prefix