import unittest
from functools import partial

import asyncio
from src.singleflightasync import SingleFlightAsync as SingleFlight

class TestSingleFlightAsync(unittest.TestCase):
  def test_call_directly(self):
    sf = SingleFlight()
    loop = asyncio.new_event_loop()

    # success case
    counter = 0
    result = "this is the result"
    async def work(num):
      nonlocal counter, result
      await asyncio.sleep(0.1) # emulate bit slower call
      counter += 1
      return (result, num)

    res = []
    async def call_directly_success_main():
      nonlocal res
      for i in range(10):
        g = loop.create_task(
          sf.call(work, "key", i+1))
        res.append(g)
      await asyncio.gather(*res)
    loop.run_until_complete(call_directly_success_main())

    for r in res:
      self.assertEqual(r.result()[0],result)
      # because only the first one can get the lock 
      # and only that one request call
      self.assertEqual(r.result()[1],1)
      
    self.assertEqual(counter,1)

    # failed case
    counter_err = 0
    err = NotImplementedError("this gonna blow!")
    async def work_err():
      nonlocal counter_err, err
      await asyncio.sleep(0.1) # emulate bit slower call
      counter_err += 1
      raise err

    res = []
    async def call_directly_failed_main():
      for i in range(10):
        g = asyncio.create_task(
          sf.call(work_err, "key_err"))
        res.append(g)
      
      # for the test, do not throw here
      # just hold the value to check later
      try: await asyncio.gather(*res)
      except: pass
    
    loop.run_until_complete(
      call_directly_failed_main())

    exception_count = 0
    for r in res:
      self.assertEqual(
        NotImplementedError, 
        type(r.exception()))
      exception_count += 1

    self.assertEqual(exception_count, 10)
    self.assertEqual(counter_err, 1)

    loop.close()

  def test_call_decorated(self):
    sf = SingleFlight()
    loop = asyncio.new_event_loop()

    # success case
    counter = 0
    result = "this is the result"

    @sf.wrap
    async def work(num):
      nonlocal counter, result
      await asyncio.sleep(0.1) # emulate bit slower call
      counter += 1
      return (result, num)

    res = []
    async def call_decorated_success_main():
      for i in range(10):
        g = loop.create_task(work("key", i+1))
        res.append(g)
      await asyncio.gather(*res)
    loop.run_until_complete(call_decorated_success_main())

    for r in res:
      self.assertEqual(r.result()[0],result)
      # because only the first one can get the lock 
      # and only that one request call
      self.assertEqual(r.result()[1],1) 
      
    self.assertEqual(counter,1)

    # failed case
    counter_err = 0
    err = NotImplementedError("this gonna blow!")

    @sf.wrap
    async def work_err():
      nonlocal counter_err, err
      await asyncio.sleep(0.1) # emulate bit slower call
      counter_err += 1
      raise err

    res = []
    async def call_decorated_failed_main():
      for i in range(10):
        g = loop.create_task(work_err("key_err"))
        res.append(g)
      
      # for the test, do not throw here
      # just hold the value to check later
      try: await asyncio.gather(*res)
      except: pass
    
    loop.run_until_complete(call_decorated_failed_main())

    exception_count = 0
    for r in res:
      self.assertEqual(
        NotImplementedError, 
        type(r.exception()))
      exception_count += 1

    self.assertEqual(exception_count, 10)
    self.assertEqual(counter_err, 1)

    loop.close()

  def test_wrong_type_passed(self):
    sf = SingleFlight()
    loop = asyncio.new_event_loop()

    def foo():
      return "fooooooo.............."

    # key is not a str
    r = loop.create_task(sf.call(foo, 1))
    self.assertRaises(
      TypeError,
      partial(loop.run_until_complete, r)
    )

    # fn is not a callable
    r = loop.create_task(sf.call(1, foo()))
    self.assertRaises(
      TypeError,
      partial(loop.run_until_complete, r)
    )
  
    loop.close()
