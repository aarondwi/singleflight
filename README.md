# singleflight

[![Build Status](https://travis-ci.org/aarondwi/singleflight.svg?branch=master)](https://travis-ci.org/aarondwi/singleflight)

Coalesce multiple identical call into one, preventing thundering-herd/stampede to database/other backends

It is a python port of [golang's groupcache singleflight implementation](https://github.com/golang/groupcache/blob/master/singleflight/singleflight.go)

This module **does not** provide caching mechanism. Rather, this module can used behind a caching abstraction to deduplicate cache-filling call

Only support python 3.5+

Installation
-----------------------

```python
pip install singleflight
```

Usage
-----------------------

This modules has 3 implementation, which can be imported as follows

```python
from singleflight.basic import SingleFlight # for multi-threaded apps
from singleflight.gevent import SingleFlightGevent as SingleFlight # for gevent apps
from singleflight.asynchronous import SingleFlightAsync as SingleFlight # for asyncio/curio apps
```

Then you can use it as follows (the example shows the multi-threaded version). Note that, `key` is important for the modules to know which call should be de-duplicated

```python
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from singleflight.basic import SingleFlight

if __name__ == '__main__':
  sf = SingleFlight()
  executor = ThreadPoolExecutor(max_workers=10)

  counter = 0
  result = "this is the result"
  def work(num):
    global counter, result
    sleep(0.1) # emulate bit slower call
    counter += 1
    return (result, num)

  res = []
  for i in range(10):
    sfc = partial(sf.call, work, "key", i+1)
    r = executor.submit(sfc)
    res.append(r)

  for r in res:
    assert r.result()[0] == result
    # because only the first one can get the lock
    # and only that one request call
    assert r.result()[1] == 1
  
  assert counter == 1
```

For decorator fans, you can also use it to wrap your function.

```python
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from singleflight.basic import SingleFlight

if __name__ == '__main__':
  sf = SingleFlight()
  executor = ThreadPoolExecutor(max_workers=10)

  # success case
  counter = 0
  result = "this is the result"

  @sf.wrap
  def work(num):
    global counter, result
    sleep(0.1) # emulate bit slower call
    counter += 1
    return (result, num)

  res = []
  for i in range(10):
    sfc = partial(work, "key", i+1)
    r = executor.submit(sfc)
    res.append(r)

  for r in res:
    assert r.result()[0] == result
    # because only the first one can get the lock
    # and only that one request call
    assert r.result()[1] == 1
  
  assert counter == 1
```

All `*args` and `**kwargs` your function has is passed directly later. Exceptions are also raised normally.
