import itertools

class AutoRegistry(object):
	""" Collection of key-value relationships with option to
	auto-register entry via decorator.
	Usage:
	my_registry = AutoRegistry()

	@my_registry('function')
	def my_func():
		...
	
	@my_registry('class')
	class MyClass:
		pass

	my_registry['function'] == function
	my_registry['class'] == MyClass
	"""
	def __init__(self):
		self._entries = {} # name: entry
	def __call__(self, name):
		""" Decorator to register entry under given name.
		Raises KeyError on attempt to register another entry to the same name.
		"""
		def _actual(cls_or_func):
			if name in self._entries:
				raise KeyError('Entry with name {0} is already registered ({1})'.format(repr(name), repr(self._entries[name])))
			self._entries[name] = cls_or_func
			return cls_or_func
		return _actual
	def __getitem__(self, name):
		""" Returns registered entry by name. May raise KeyError. """
		return self._entries[name]
	def __iter__(self):
		""" Returns iterable of all registered entry values. """
		return iter(self.values())
	def keys(self):
		""" Returns iterable of all registered entry names. """
		return self._entries.keys()
	def values(self):
		""" Returns iterable of all pairs of registered values. """
		return self._entries.values()
	def items(self):
		""" Returns iterable of all pairs of registered names and values. """
		return self._entries.items()

class dotdict(dict):
	""" Dict that support dotted access:
	  d['value']['nested_value'] == d.value.nested_value

	<https://stackoverflow.com/a/23689767/2128769>
	"""
	def __getattr__(self, attr):
		value = dict.get(self, attr)
		return dotdict(value) if type(value) is dict else value
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__
	def __getstate__(self):
		return dict(self)
	def __setstate__(self, data):
		self.clear()
		self.update(data)

class Enum(object):
	""" Enumeration of integer type with auto-increment.
	Example:
	class MyEnum(Enum):
		auto = Enum.auto(3) # Initializes auto-increment. Default start is 1.
		FIRST = auto() # => 3
		SECOND = auto() # => 4
		THIRD = auto() # => 5
	"""
	class auto(object):
		def __init__(self, start_value=1):
			self._iter = itertools.count(start_value)
		def __call__(self):
			""" Returns next free value. """
			return next(self._iter)
	@classmethod
	def _all(cls):
		""" Returns dict of all values: {name:value} """
		return {key:getattr(cls, key) for key in cls.__dict__ if not key.startswith('_') and type(getattr(cls, key)) is int}
	@classmethod
	def _top(cls):
		""" Returns the last (topmost) generated value. """
		return max(cls._all().values())
