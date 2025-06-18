class Event(object):
	""" Base class for any game event.
	Define classfield FIELDS which should list event properties. They will be available as event object's fields.
	FIELDS should be either iterable (tuple, list) or a string for words separated by spaces.
	"""
	FIELDS = NotImplemented
	def __init__(self, *args, **kwargs):
		""" Accepts and sets event properties, either as positional or as keyword args.
		"""
		fields = self.FIELDS.split() if isinstance(self.FIELDS, str) else self.FIELDS
		for arg, value in zip(fields, args):
			setattr(self, arg, value)
		for kwarg, value in kwargs.items():
			assert kwarg in fields
			setattr(self, kwarg, value)
	def __repr__(self):
		fields = self.FIELDS.split() if isinstance(self.FIELDS, str) else self.FIELDS
		return '{0}({1})'.format(self.__class__.__name__, ', '.join(('{0}={1}'.format(name, getattr(self, name)) for name in fields)))

class Events:
	""" Registry of convertors of events to string (or other) representation to display on UI. """
	_registry = {}
	@classmethod
	def on(cls, event_type):
		""" Registers callback for given event type. """
		def _actual(f):
			cls._registry[event_type] = f
			return f
		return _actual
	@classmethod
	def get(cls, event, bind_self=None):
		""" Returns callback for given event.
		If bind_self is given, considers callback a method
		and binds it to the given instance.
		Useful when callbacks accept more arguments than just event.
		"""
		callback = cls._registry.get(type(event))
		if not callback:
			return None
		if bind_self:
			callback = callback.__get__(bind_self, type(bind_self))
		return callback
	@classmethod
	def process(cls, event, bind_self=None):
		""" Processes event by executing bound callback.
		Callback should accept single argument: event object.
		See .get() for details.
		"""
		return cls.get(event, bind_self=bind_self)(event)
