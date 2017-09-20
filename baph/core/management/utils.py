

def get_parser_options(parser):
  options = set()
  for action in parser._optionals._actions:
    options.update(action.option_strings)
  return options

def get_command_options(command):
  parser = command.create_parser('test', 'test')
  return get_parser_options(parser)