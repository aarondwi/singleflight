import unittest
from functools import partial

from gevent import spawn, joinall, sleep

from singleflight.gevent import SingleFlightGevent as SingleFlight

class TestSingleFlightGevent(unittest.TestCase):
  def test_call_directly(self):
    sf = SingleFlight()

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
      p = partial(sf.call, work, "key", i+1)
      g = spawn(p)
      res.append(g)
    joinall(res)

    for r in res:
      self.assertEqual(r.value[0],result)
      # because only the first one can get the lock 
      # and only that one request call
      self.assertEqual(r.value[1],1)
      
    self.assertEqual(counter,1)

    # failed case
    counter_err = 0
    err = NotImplementedError("this gonna blow!")
    def work_err():
      nonlocal counter_err, err
      sleep(0.1) # emulate bit slower call
      counter_err += 1
      raise err

    res = []
    for i in range(10):
      p = partial(sf.call, work_err, "key_err")
      g = spawn(p)
      res.append(g)
    joinall(res)

    exception_count = 0
    for r in res:
      self.assertEqual(
        NotImplementedError, 
        type(r.exception))
      exception_count += 1

    self.assertEqual(exception_count, 10)
    self.assertEqual(counter_err, 1)

  def test_call_decorated(self):
    sf = SingleFlight()

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
      p = partial(work, "key", i+1)
      g = spawn(p)
      res.append(g)
    joinall(res)

    for r in res:
      self.assertEqual(r.value[0],result)
      # because only the first one can get the lock 
      # and only that one request call
      self.assertEqual(r.value[1],1) 
      
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

    res = []
    for i in range(10):
      p = partial(work_err, "key_err")
      g = spawn(p)
      res.append(g)
    joinall(res)

    exception_count = 0
    for r in res:
      self.assertEqual(
        NotImplementedError, 
        type(r.exception))
      exception_count += 1

    self.assertEqual(exception_count, 10)
    self.assertEqual(counter_err, 1)

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
  