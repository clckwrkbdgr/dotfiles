def with_metaclass(metaclass):
	""" Class decorator to add metaclass for Py2/Py3. """
	def decorator(cls):
		body = vars(cls).copy()
		# clean out class body
		body.pop('__dict__', None)
		body.pop('__weakref__', None)
		return metaclass(cls.__name__, cls.__bases__, body)
	return decorator

class EnumType(type):
	""" Metaclass for Enum classes. """
	def __getattr__(cls, name):
		if name == '_values':
			cls._values = [line.strip().upper() for line in cls.__doc__.splitlines() if line.strip()]
			return cls._values
		return cls._values.index(name)
	@property
	def CURRENT(self):
		return len(self._values)

@with_metaclass(EnumType)
class Enum(object):
	""" Enum values should be described in a docstring, one for line, e.g.:

	first
	Second

	All names are converted to all caps. Values start with 0. Meta value CURRENT returns the next available value (e.g. 2 in this case).
	"""
	pass

def all_subclasses(cls):
	""" Returns list of all subclasses (including not direct ones) of given new-style class. """
	return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in all_subclasses(s)]
