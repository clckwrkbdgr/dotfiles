from . import events

def is_diagonal(shift):
	return abs(shift.x) + abs(shift.y) == 2

class GodMode:
	""" God mode options.
	- vision: see through everything, ignore FOV/transparency.
	- noclip: walk through everything, ignoring obstacles.
	"""
	def __init__(self):
		self.vision = False
		self.noclip = False

class Game(object):
	""" Main object for the game mechanics.
	"""
	def __init__(self, rng=None):
		if rng is None:
			import random
			rng = random
		self.rng = rng
		self.god = GodMode()
		self.events = []
		self.scene = None

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

	# Display.

	def is_visible(self, pos): # pragma: no cover
		""" Should return True is position on map is visible to player.
		By default the whole map is visible.
		"""
		return True
	def is_visited(self, pos): # pragma: no cover
		""" Should return True is position on map was visited by player.
		By default the whole map is considered visited and remembered.
		"""
		return True

	# Actions.

	def in_automovement(self): # pragma: no cover
		""" Should return True when player's currently automoving.
		"""
		return False
	def perform_automovement(self): # pragma: no cover
		""" Should perform any automovement activities
		(if currently enabled).
		"""
		pass
	def stop_automovement(self): # pragma: no cover
		""" Force stop automovement (e.g. because of user interruption).
		"""
		pass
	def automove(self, dest=None): # pragma: no cover
		""" Start automovement to the specified destination point.
		If point is not specified, start autoexploring mode.
		"""
		raise NotImplementedError()

	def move_actor(self, actor, shift): # pragma: no cover
		""" Should move actor on scene by specified shift.
		"""
		raise NotImplementedError()

	def process_others(self): # pragma: no cover
		""" Should be called at the end of player's turn
		to process other monsters and other game mechanics.
		Should perform check for player turn manually
		and reset it also manually.
		"""
		pass
