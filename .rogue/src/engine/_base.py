from . import events

class Game(object):
	""" Main object for the game mechanics.
	"""
	def __init__(self, rng=None):
		if rng is None:
			import random
			rng = random
		self.rng = rng
		self.events = []
	def generate(self): # pragma: no cover
		""" Should reset game and generate new state.
		Common pattern is create dummy Game object
		and then explicitly call generate().
		"""
		raise NotImplementedError()
	def load(self, reader): # pragma: no cover
		""" Should load game data from the stream/state.
		"""
		raise NotImplementedError()
	def save(self, reader): # pragma: no cover
		""" Should store game data to the reader/state.
		"""
		raise NotImplementedError()
	def is_finished(self): # pragma: no cover
		""" Should return True if game is completed/finished/failed
		and should reset, e.g. savefile should be deleted.
		Otherwise game keeps going and should be saved.
		"""
		raise NotImplementedError()

	def fire_event(self, event):
		""" Adds new event to the list.
		"""
		self.events.append(event)
	def process_events(self, raw=False, bind_self=None):
		""" Iterates over accumulated events and processes them immediately,
		yielding results of the processing.
		Effectively removes each processed event.
		If raw is True, yields tuples of (raw callback, event object) instead of executing them.
		"""
		while self.events:
			event = self.events.pop(0)
			if raw:
				yield events.Events.get(event, bind_self=bind_self), event
			else:
				yield events.Events.process(event, bind_self=bind_self)
