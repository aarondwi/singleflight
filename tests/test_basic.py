import unittest

from time import sleep
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from singleflight.basic import SingleFlight

class TestSingleFlight(unittest.TestCase):
  def test_call_directly(self):
    sf = SingleFlight()
    executor = ThreadPoolExecutor(max_workers=10)

    # success case
    counter = 0
    result = "this is the result"
    def work(num):
      nonlocal counter, result
      sleep(0.1) # emulate bit slower call
      counter += 1
      return (result, num)

    res = []
    for i in range(10):
      sfc = partial(sf.call, work, "key", i+1)
      r = executor.submit(sfc)
      res.append(r)

    for r in res:
      self.assertEqual(r.result()[0],result)
      # because only the first one can get the lock 
      # and only that one request call
      self.assertEqual(r.result()[1],1) 
      
    self.assertEqual(counter,1)

    # failed case
    counter_err = 0
    err = NotImplementedError("this gonna blow!")
    def work_err():
      nonlocal counter_err, err
      sleep(0.1) # emulate bit slower call
      counter_err += 1
      raise err

    sfc_err = partial(sf.call, work_err, "key_err")
    res = []
    for i in range(10):
      r = executor.submit(sfc_err)
      res.append(r)

    exception_count = 0
    for r in res:
      self.assertRaises(NotImplementedError, r.result)
      exception_count += 1

    self.assertEqual(exception_count, 10)
    self.assertEqual(counter_err, 1)
  
    executor.shutdown()

  def test_call_decorated(self):
    sf = SingleFlight()
    executor = ThreadPoolExecutor(max_workers=10)

    # success case
    counter = 0
    result = "this is the result"

    @sf.wrap
    def work(num):
      nonlocal counter, result
      sleep(0.1) # emulate bit slower call
      counter += 1
      return (result, num)

    res = []
    for i in range(10):
      sfc = partial(work, "key", i+1)
      r = executor.submit(sfc)
      res.append(r)

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
    def work_err():
      nonlocal counter_err, err
      sleep(0.1) # emulate bit slower call
      counter_err += 1
      raise err

    sfc_err = partial(work_err, "key_err")
    res = []
    for i in range(10):
      r = executor.submit(sfc_err)
      res.append(r)

    exception_count = 0
    for r in res:
      self.assertRaises(NotImplementedError, r.result)
      exception_count += 1

    self.assertEqual(exception_count, 10)
    self.assertEqual(counter_err, 1)

    executor.shutdown()
      
  def test_wrong_type_passed(self):
    sf = SingleFlight()

    def foo():
      return "fooooooo.............."

    # key is not a str
    key_err_partial = partial(sf.call, foo, 1)
    self.assertRaises(TypeError, key_err_partial)

    # fn is not a callable
    fn_err_partial = partial(sf.call, 1, foo())
    self.assertRaises(TypeError, fn_err_partial)
  