from importlib import import_module
import inspect

from django.conf import settings
from django.utils.functional import cached_property
import sqlalchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from baph.utils.module_loading import import_string


class FrameProcessor(object):
  __slots__ = ['apps', 'args']

  @cached_property
  def app_paths(self):
    app_paths = []
    for app in self.apps:
      name = app.rsplit('.', 1)[-1]
      mod = import_module(app)
      path = mod.__path__[0]
      app_paths.append((name, path))
    return app_paths

  def get_app(self, path):
    for name, app_path in self.app_paths:
      if path.startswith(app_path):
        return name

  def _should_run(self, path, context):
    if not self.get_app(path):
      return False
    return self.should_run(path, context)

  def should_run(self, path, context):
    return True

  def __call__(self, frame, context):
    raise NotImplemented()

def resolve_entity(entity):
  if hasattr(entity, 'class_'):
    # this is a mapper
    entity = entity.class_
  return entity.__name__

class SQLAlchemyFrameProcessor(FrameProcessor):
  apps = ['sqlalchemy']
  args = ['op', 'entity']

  def __call__(self, frame, context):
    frame, path, lineno, func_name, lines, index = frame
    args = inspect.getargvalues(frame).locals

    if func_name == '_emit_lazyload':
      op = 'lazyload'
      entity = str(args['self'])
    elif func_name == '_emit_insert_statements':
      op = 'insert'
      entity = resolve_entity(args['mapper'])
    elif func_name == 'scalar':
      op = 'load scalar'
      col_entity = args['self']._entity_zero()
      entity = str(col_entity)
      if str(entity).startswith('count('):
        op = 'count'
        entity = resolve_entity(col_entity.entity_zero)
    elif func_name == '_load_expired':
      op = 'load expired'
      entity = resolve_entity(type(args['state'].object))
    elif func_name in ('first', 'one'):
      op = 'load'
      entity = resolve_entity(args['self']._mapper_zero())
    elif func_name == '__getitem__':
      op = 'load multi'
      entity = resolve_entity(args['self']._mapper_zero())
    else:
      return
    context['op'] = op
    context['entity'] = entity

class QueryLogger(object):
  __slots__ = ['queries', 'emit', 'processors', 'args']

  def __init__(self, emit=False):
    self.emit = emit
    self.args = []
    self.processors = [SQLAlchemyFrameProcessor()]
    for path in getattr(settings, 'QUERY_FRAME_PROCESSORS', []):
      proc = import_string(path)
      self.processors.append(proc())
    for proc in self.processors:
      self.args.extend(proc.args)

  def __enter__(self):
    event.listen(Engine, 'before_cursor_execute', self.callback)
    self.queries = []
    return self

  def __exit__(self, *exc):
    event.remove(Engine, 'before_cursor_execute', self.callback)
    return False

  def process_stack(self):
    info = {k: None for k in self.args}
    for frame in inspect.stack():
      path = frame[1]
      for proc in self.processors:
        if proc._should_run(path, info):
          proc(frame, info)

    return info

  def callback(self, conn, cursor, stmt, params, context, executemany):
    info = self.process_stack()
    self.queries.append((stmt, params, info))
    if self.emit:
      print '\n[QUERY]:', self.queries[-1]

  @property
  def count(self):
    return len(self.queries)

  def get_identity(self, info):
    return tuple(info[k] for k in self.args)

  @property
  def identities(self):
    return [self.get_identity(info) for _, _, info in self.queries]

class QueryLoggerMixin(object):

  @property
  def querylogger(self):
    if not hasattr(self, '_querylogger'):
      self._querylogger = QueryLogger()
    return self._querylogger

  @property
  def verbose_querylogger(self):
    if not hasattr(self, '_querylogger'):
      self._querylogger = QueryLogger(emit=True)
    return self._querylogger

  def assertQuerysetMatches(self, queryset):
    results = self._querylogger.identities[:]
    self.assertLessEqual(len(results), len(queryset),
      'Expected a maximum of %d queries, but %d were executed:\n%s'
      % (len(queryset), len(results), '\n'.join(str(q) for q in results))
    )
    queryset = queryset[:]
    while queryset:
      query = queryset.pop(0)
      if query[-1] == 'optional':
        query = query[:-1]
        optional = True
      else:
        optional = False
      if all(query[i] in ('*', results[0][i]) for i in range(len(query))):
        results.pop(0)
        continue
      if optional:
        continue
      raise AssertionError('query identity %s not found in results'
        % str(query))
