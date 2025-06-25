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
	
	# State control.

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

	# Events.

	def fire_event(self, event):
		""" Adds new event to the list.
		"""
		self.events.append(event)
	def has_unprocessed_events(self):
		""" Returns True if there are unprocessed events left. """
		return bool(self.events)
	def process_next_event(self, raw=False, bind_self=None):
		""" Immediately processes next event from the event queue,
		returning results of the processing.
		Effectively removes each processed event.
		If raw is True, yields tuples of (raw callback, event object) instead of executing them.
		"""
		event = self.events.pop(0)
		if raw:
			return events.Events.get(event, bind_self=bind_self), event
		else:
			return events.Events.process(event, bind_self=bind_self)
	def process_events(self, raw=False, bind_self=None):
		""" Iterates over accumulated events and processes them immediately,
		yielding results of the processing.
		Effectively removes each processed event.
		If raw is True, yields tuples of (raw callback, event object) instead of executing them.
		"""
		while self.has_unprocessed_events():
			yield self.process_next_event(raw=raw, bind_self=bind_self)
	
	# Queries and info.

	def get_cell_info(self, pos, context=None): # pragma: no cover
		""" Should return cell info in form of tuples for given world position:
		(terrain, [objects on that cell], [items on that cell], [monsters on that cell]).
		Terrain may be None. Any list may be empty.
		Entities in lists should be sorted bottom-to-top.
		Monster list should include player if present.
		No visibility/remembered state should be checked at this stage. This is raw info.

		Additional context data may be passed with some cached calculations
		(usually within loops like iter_cells()).
		"""
	def iter_cells(self, view_rect): # pragma: no cover
		""" Should yield cell info for each position in the given boundaries:
		(world pos, cell info)
		See get_cell_info() for details.
		"""
		raise NotImplementedError()
	def get_player(self): # pragma: no cover
		""" Should return player-controlled actor character. """
		raise NotImplementedError()
