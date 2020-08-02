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
		""" Returns iterable of all registered entry names. """
		return iter(self.keys())
	def keys(self):
		""" Returns iterable of all registered entry names. """
		return self._entries.keys()

