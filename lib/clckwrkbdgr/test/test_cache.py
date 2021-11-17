import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import inspect
import clckwrkbdgr.cache
from clckwrkbdgr.cache import CacheKey, cached

class MockStorage(clckwrkbdgr.cache.CacheStorage):
	def __init__(self):
		self.data = {}
		self.requests = []
	def has(self, key):
		self.requests.append( ('has', key) )
		return key in self.data
	def get(self, key):
		self.requests.append( ('get', key) )
		return self.data[key]
	def update(self, key, new_value):
		self.requests.append( ('update', key) )
		self.data[key] = new_value

class MockInvalidator(clckwrkbdgr.cache.Invalidator):
	def __init__(self, invalid_keys):
		self.invalid = invalid_keys
	def is_invalid(self, key):
		return key in self.invalid

class TestCache(unittest.TestCase):
	def should_cache_data(self):
		def f(value):
			return value * value
		name = inspect.getmodule(f).__name__ + '.' + f.__name__

		storage = MockStorage()
		invalidator = MockInvalidator({})

		f = cached(storage, invalidator)(f)

		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('update', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('get', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('update', CacheKey(name, (2,), tuple())),
			])

		invalidator.invalid = {CacheKey(name, (2,), tuple())}
		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('update', CacheKey(name, (2,), tuple())),
			])
	def should_cache_generator(self):
		def f(value):
			for i in range(value):
				yield i
		name = inspect.getmodule(f).__name__ + '.' + f.__name__

		storage = MockStorage()
		invalidator = MockInvalidator({})

		f = cached(storage, invalidator)(f)

		self.assertEqual(f(1), [0])
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('update', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(1), [0])
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('get', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), [0, 1])
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('update', CacheKey(name, (2,), tuple())),
			])

		invalidator.invalid = {CacheKey(name, (2,), tuple())}
		storage.requests = []
		self.assertEqual(f(2), [0, 1])
		self.assertEqual(storage.requests, [
			('update', CacheKey(name, (2,), tuple())),
			])
	def should_force_fallback_to_cache(self):
		side_effect = [True, True, False, True, False]
		def f(value):
			ok = side_effect.pop(0)
			if not ok:
				raise clckwrkbdgr.cache.FallbackToCache()
			return value * value
		name = inspect.getmodule(f).__name__ + '.' + f.__name__

		storage = MockStorage()
		invalidator = MockInvalidator({})

		f = cached(storage, invalidator)(f)

		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('update', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('get', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('update', CacheKey(name, (2,), tuple())),
			])

		invalidator.invalid = {CacheKey(name, (2,), tuple())}
		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('get', CacheKey(name, (2,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('update', CacheKey(name, (2,), tuple())),
			])

		with self.assertRaises(clckwrkbdgr.cache.FallbackToCache):
			f(3)
	def should_fallback_to_cache_on_exception(self):
		side_effect = [True, True, False, True, False]
		def f(value):
			ok = side_effect.pop(0)
			if not ok:
				raise RuntimeError()
			return value * value
		name = inspect.getmodule(f).__name__ + '.' + f.__name__

		storage = MockStorage()
		invalidator = MockInvalidator({})

		f = cached(storage, invalidator, print_traceback=False)(f)

		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('update', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('get', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('update', CacheKey(name, (2,), tuple())),
			])

		invalidator.invalid = {CacheKey(name, (2,), tuple())}
		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('get', CacheKey(name, (2,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('update', CacheKey(name, (2,), tuple())),
			])

		with self.assertRaises(RuntimeError):
			f(3)
	def should_raise_on_exception_if_requested(self):
		side_effect = [True, True, False, True, False]
		def f(value):
			ok = side_effect.pop(0)
			if not ok:
				raise RuntimeError()
			return value * value
		name = inspect.getmodule(f).__name__ + '.' + f.__name__

		storage = MockStorage()
		invalidator = MockInvalidator({})

		f = cached(storage, invalidator, restore_on_exception=False, print_traceback=False)(f)

		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('update', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(1), 1)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (1,), tuple())),
			('get', CacheKey(name, (1,), tuple())),
			])

		storage.requests = []
		self.assertEqual(f(2), 4)
		self.assertEqual(storage.requests, [
			('has', CacheKey(name, (2,), tuple())),
			('update', CacheKey(name, (2,), tuple())),
			])

		invalidator.invalid = {CacheKey(name, (2,), tuple())}
		storage.requests = []
		with self.assertRaises(RuntimeError):
			f(2)
		self.assertEqual(storage.requests, [
			])
