import six, inspect

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
	def __eq__(self, other):
		if type(self) != type(other):
			return False
		fields = self.FIELDS.split() if isinstance(self.FIELDS, str) else self.FIELDS
		for field in fields:
			if getattr(self, field) != getattr(other, field):
				return False
		return True

class ImportantEvent(Event):
	""" Base class for events that may not be ignored.
	Encountering this event should abort any auto-activity.
	E.g. discovering new features, encountering monsters etc.
	"""
	pass

class Events:
	""" Registry of convertors of events to string (or other) representation to display on UI. """
	class NotRegistered(RuntimeError):
		def __init__(self, event_type):
			self.event_type = event_type
		def __str__(self):
			return "Event not registered: {0}".format(self.event_type)

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
		if six.PY2: # pragma: no cover
			is_method = inspect.getargspec(callback)
		else: # pragma: no cover -- TODO very stupid way to distinct functions that should be bound method and non-method functions.
			is_method = next(iter(inspect.signature(callback).parameters.keys())) == 'self'
		if is_method and bind_self:
			callback = callback.__get__(bind_self, type(bind_self))
		return callback
	@classmethod
	def process(cls, event, bind_self=None):
		""" Processes event by executing bound callback.
		Callback should accept single argument: event object.
		See .get() for details.
		May throw NotRegistered.
		"""
		callback = cls.get(event, bind_self=bind_self)
		if callback is None:
			raise cls.NotRegistered(type(event))
		return callback(event)
