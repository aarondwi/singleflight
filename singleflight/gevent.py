"""singleflight api implementation for gevent"""

from gevent import sleep as gv_sleep
from gevent.threading import Lock as gv_lock
from gevent.event import Event as gv_event
from typing import Callable
from functools import wraps, partial

__all__ = ['SingleFlightGevent']

class CallLockGevent(object):
  """
  A gevent implementation of SingleFlight CallLock

  This implementation use gevent's version for event
  not the monkey-patched version (should be the same in effect though)
  """
  def __init__(self):
    super().__init__()
    self.ev = gv_event()
    self.res = None
    self.err = None

class SingleFlightGevent(object):
  """
  SingleFlight's support of gevent api

  An application only need one of this object, 
  as it can manage lots of call at the same time

  This implementation use gevent's version for sleep and lock
  not the monkey-patched version
  """
  def __init__(self):
    super().__init__()
    self.lock = gv_lock()
    self.m = {}

  def call(self, fn: Callable[[any], any], key: str, *args, **kwargs) -> any:
    """
    Call `fn` with the given `*args` and `**kwargs` exactly once

    `key` are used to detect and coalesce duplicate call

    `key` is only hold for the duration of this function, after that it will be removed and `key` can be used again
    """
    if not isinstance(key, str):
      raise TypeError("Key should be a str")
    if not isinstance(fn, Callable):
      raise TypeError("fn should be a callable")

    # this part does not use with-statement
    # because the one need to be waited is different object (self.lock vs self.m[key].ev)
    self.lock.acquire(True)
    if key in self.m:
      # key exists here means 
      # another thread is currently making the call
      # just need to wait
      cl = self.m[key]
      self.lock.release()
      cl.ev.wait()

      if cl.err:
        raise cl.err
      return cl.res

    cl = CallLockGevent()
    self.m[key] = cl
    self.lock.release()

    try:
      cl.res = fn(*args, **kwargs)
      cl.err = None
    except Exception as e:
      cl.res = None
      cl.err = e
    finally:
      cl.ev.set()
    
    # delete the calllock, so next call
    # with same key can pass through
    with self.lock:
      del(self.m[key])

    if cl.err is not None:
      raise cl.err
    return cl.res

  def wrap(self, fn: Callable[[any], any]):
    """ simple wrapper for SingleFlightGevent.call """
    @wraps(fn)
    def wrapper(*args, **kwargs):
      return partial(self.call, fn, *args, **kwargs)

    return wrapper()
