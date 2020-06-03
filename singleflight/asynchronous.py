"""singleflight api implementation for asyncio/curio"""

from asyncio import (
  Lock as async_lock, 
  sleep as async_sleep, 
  Event as async_event
)
from typing import Callable
from functools import wraps, partial

__all__ = ['SingleFlightAsync']

class CallLockAsync(object):
  """
  An async implementation of SingleFlight CallLock
  """
  def __init__(self):
    super().__init__()
    self.ev = async_event()
    self.res = None
    self.err = None

class SingleFlightAsync(object):
  """
  SingleFlight's support of python's async/await (with asyncio/curio)

  Contrast to SingleFlight class, this class is not thread-safe. 
  You should only use this class when paired with async apps (asyncio/curio/the likes)
  """
  def __init__(self):
    super().__init__()
    self.lock = async_lock()
    self.m = {}

  async def call(self, fn: Callable[[any], any], key: str, *args, **kwargs) -> any:
    """
    Asynchronously call `fn` with the given `*args` and `**kwargs` exactly once

    `key` are used to detect and coalesce duplicate call

    `key` is only hold for the duration of this function, after that it will be removed and `key` can be used again
    """
    if not isinstance(key, str):
      raise TypeError("Key should be a str")
    if not isinstance(fn, Callable):
      raise TypeError("fn should be a callable")

    # this part does not use with-statement
    # because the one need to be waited is different object (self.lock vs self.m[key].ev)
    await self.lock.acquire()
    if key in self.m:
      # key exists here means 
      # another thread is currently making the call
      # just need to wait
      self.lock.release()
      await self.m[key].ev.wait()

      if self.m[key].err:
        raise self.m[key].err
      return self.m[key].res

    cl = CallLockAsync()
    self.m[key] = cl
    self.lock.release()

    try:
      cl.res = await fn(*args, **kwargs)
      cl.err = None
    except Exception as e:
      cl.res = None
      cl.err = e

    # give time for other threads to get value
    # or raising error (if any)
    # adding sleep a bit (currently hardcoded to 5ms) is still better
    # than database/any backend got stampeded
    cl.ev.set()
    await async_sleep(0.005)
    
    # delete the calllock, so next call
    # with same key can pass through
    async with self.lock:
      del(self.m[key])

    if cl.err is not None:
      raise cl.err
    return cl.res

  def wrap(self, fn: Callable[[any], any]):
    """ simple wrapper for SingleFlightAsync.call """
    @wraps(fn)
    def wrapper(*args, **kwargs):
      return partial(self.call, fn, *args, **kwargs)

    return wrapper()
