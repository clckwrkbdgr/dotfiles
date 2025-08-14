import logging
Log = logging.getLogger('rogue')
from . import events
from . import auto

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
		self.playing_time = 0
		self.god = GodMode()
		self.events = []
		self.scene = None
		self.automovement = None

	# State control.

	def make_player(self): # pragma: no cover
		""" Should return constructed player's Actor,
		ready to be added on the scene (pos does not matter).
		"""
		raise NotImplementedError()
	def make_scene(self, scene_id): # pragma: no cover
		""" Should return constructed Scene object for given ID. """
		raise NotImplementedError()
	def generate(self, start_scene_id): # pragma: no cover
		""" Should reset game and generate new state.
		Starts with given scene and places player (see make_player())
		at the default location (see Scene.enter_actor).
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
	def is_finished(self):
		""" Should return True if game is completed/finished/failed
		and should reset, e.g. savefile should be deleted.
		Otherwise game keeps going and should be saved.
		By default checks if player character is still alive
		"""
		return not (self.scene.get_player() and self.scene.get_player().is_alive())

	# Events.

	def fire_event(self, event):
		""" Adds new event to the list.
		"""
		self.events.append(event)
	def has_unprocessed_events(self, important_only=False):
		""" Returns True if there are unprocessed events left.
		If important_only=True, checks only for ImportantEvent items,
		ignoring the rest.
		"""
		if important_only:
			return next((True for event in self.events if isinstance(event, events.ImportantEvent)), False)
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

	def in_automovement(self):
		""" Returns True when player's currently automoving.
		"""
		return self.automovement is not None
	def perform_automovement(self):
		""" Should perform any automovement activities
		(if currently enabled).
		"""
		""" Performs next step from auto-movement queue,
		if any and until available.
		Stops on important events.
		"""
		if not self.automovement:
			return False
		if self.has_unprocessed_events(important_only=True):
			Log.debug('New events in FOV, aborting auto-moving mode.')
			self.automovement = None
			return False
		Log.debug('Performing queued actions.')
		shift = self.automovement.next()
		if not shift:
			self.automovement = None
			return False
		self.move_actor(self.scene.get_player(), shift)
		return True
	def stop_automovement(self):
		""" Force stop automovement (e.g. because of user interruption).
		"""
		self.automovement = None
	def automove(self, dest=None):
		""" Start automovement to the specified destination point.
		If point is not specified, start autoexploring mode.
		"""
		if self.prevent_automove():
			return False
		if dest is None:
			self.automovement = self.scene.get_autoexplorer_class()(self)
		else:
			self.automovement = auto.AutoWalk(self, dest)
		return True
	def prevent_automove(self): # pragma: no cover
		""" Should return True if there are any conditions at play
		that prevent auto movement from start (e.g. visible danger)
		"""
		return False

	def move_actor(self, actor, shift): # pragma: no cover
		""" Should move actor on scene by specified shift.
		"""
		raise NotImplementedError()

	def process_others(self): # pragma: no cover
		""" Should be called at the end of player's turn
		to process other monsters and other game mechanics.
		Perform check for player turn manually
		and reset it also manually.
		Applies any auto effects on player.
		Performs actions for all other monsters in the activity area
		(see Scene.iter_active_monsters).
		Forwards playing time.
		"""
		if not (self.scene.get_player() and self.scene.get_player().has_acted()):
			return False
		self.scene.get_player().apply_auto_effects()
		self.scene.get_player().add_action_points()

		for monster in list(self.scene.iter_active_monsters()):
			if monster == self.scene.get_player():
				continue
			monster.act(self)

		self.playing_time += 1
		return True
