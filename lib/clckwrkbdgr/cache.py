from __future__ import absolute_import
import types
import functools, inspect
from collections import namedtuple

CacheKey = namedtuple('CacheKey', 'func_key args kwargs')

class CacheStorage(object):
	""" Basic interface for cache storage.
	Does not perform invalidation, only stores cached entities.
	"""
	def has(self, key): # pragma: no cover
		""" Should return True if cache contains a key. """
		raise NotImplementedError
	def get(self, key): # pragma: no cover
		""" Should return entity by key.
		May raise exception if there is no such key.
		"""
		raise NotImplementedError
	def update(self, key, new_value): # pragma: no cover
		""" Should update entity in storage for given key. """
		raise NotImplementedError

class Invalidator(object):
	""" Basic interface for invalidator. """
	def is_invalid(self, key): # pragma: no cover
		""" Should return True if object with given key was invalidated and should be recalculated.
		"""
		raise NotImplementedError

class FallbackToCache(RuntimeError):
	""" May be raised by client function to indicate that real value cannot be recalculated
	and cached value should be used instead.
	In case when no such key is cached yet, may fall through.
	"""
	pass

class Cache(object):
	""" Caches result of function call.

	Returns cached value instead of calling client function if key in present in cache.
	Cache key consists of full qualified function name and arguments (they should be hashable).
	Generator functions will be drained for all values and result will be a list instead.

	Better used via @cached() decorator.
	"""
	def __init__(self, func, cache_storage, invalidator, restore_on_exception=True, print_traceback=True):
		""" Creates cache for given function,
		using given cache storage and invalidation strategy.
		If restore_on_exception is True, tries to hinder the exception and to pick cached values in case when client function raises an exception.
		If print_traceback is True, prints traceback to stdout in such cases.
		If restore_on_exception is False, exception falls through to calling code.
		"""
		self.func = func
		functools.update_wrapper(self, func)
		self.__wrapped__ = func
		self.storage = cache_storage
		self.invalidator = invalidator
		self.restore_on_exception = restore_on_exception
		self.print_traceback = print_traceback
	def __call__(self, *args, **kwargs):
		func_key = inspect.getmodule(self.func).__name__ + '.' + self.func.__name__
		key = CacheKey(func_key, args, tuple((k,v) for k,v in sorted(kwargs.items())))
		if self.invalidator.is_invalid(key):
			return self._actual_call(key, *args, **kwargs)
		if self.storage.has(key):
			result = self.storage.get(key)
			return result
		return self._actual_call(key, *args, **kwargs)
	def _actual_call(self, key, *args, **kwargs):
		try:
			result = self.func(*args, **kwargs)
			if isinstance(result, types.GeneratorType):
				result = list(result)
		except FallbackToCache:
			if self.storage.has(key):
				result = self.storage.get(key)
				return result
			else:
				raise
		except Exception as e:
			if self.restore_on_exception and self.storage.has(key):
				if self.print_traceback: # pragma: no cover
					import traceback
					traceback.print_exc()
				result = self.storage.get(key)
				return result
			else:
				raise
		self.storage.update(key, result)
		return result

def cached(cache_storage, invalidator, restore_on_exception=True, print_traceback=True):
	""" Adds cache to function.
	See class Cache for details on behavior and parameters.

	Usage:

	@cached(...)
	def f(...):
		return ...
	"""
	def _wrapper(func):
		return Cache(func, cache_storage, invalidator, restore_on_exception=restore_on_exception, print_traceback=print_traceback)
	return _wrapper
