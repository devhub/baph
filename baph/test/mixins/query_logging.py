from sqlalchemy import event
from sqlalchemy.engine import Engine


class QueryLogger(object):
  __slots__ = ['queries', 'emit']

  def __init__(self, emit=False):
    self.emit = emit

  def __enter__(self):
    event.listen(Engine, 'before_cursor_execute', self.callback)
    self.queries = []
    return self

  def __exit__(self, *exc):
    event.remove(Engine, 'before_cursor_execute', self.callback)
    return False

  def callback(self, conn, cursor, stmt, params, context, executemany):
    self.queries.append((stmt, params))
    if self.emit:
      print '\n[QUERY]:', self.queries[-1]

  @property
  def count(self):
    return len(self.queries)

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