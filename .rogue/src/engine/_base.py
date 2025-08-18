import logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.pcg import RNG
from . import events
from . import scene
from . import auto

class GodMode:
	""" God mode options.
	- vision: see through everything, ignore FOV/transparency.
	- noclip: walk through everything, ignoring obstacles.
	"""
	def __init__(self):
		self.vision = False
		self.noclip = False

class Events:
	class StareIntoVoid(events.Event):
		""" No movement past the edge of the world. """
		FIELDS = ''
	class BumpIntoTerrain(events.Event):
		""" Bumps into impenetrable obstacle. """
		FIELDS = 'actor target'

class Game(object):
	""" Main object for the game mechanics.
	"""
	def __init__(self, rng=None):
		if rng is None:
			import time
			rng = RNG(int(time.time()))
		self.rng = rng
		self.playing_time = 0
		self.god = GodMode()
		self.events = []
		self.scenes = {}
		self.current_scene_id = None
		self.automovement = None
	@property
	def scene(self):
		return self.scenes[self.current_scene_id]

	# State control.

	def make_player(self): # pragma: no cover
		""" Should return constructed player's Actor,
		ready to be added on the scene (pos does not matter).
		"""
		raise NotImplementedError()
	def make_scene(self, scene_id): # pragma: no cover
		""" Should return constructed Scene object for given ID. """
		raise NotImplementedError()
	def travel(self, actor, scene_id, passage=None):
		""" Travel to a specified scene.
		Creates the scene, if necessary.
		Places actor at the LevelPassage with specified ID.
		If passage is None, picks the default location
		(see Scene.enter_actor).
		Actor should be present on the current scene (if there is any).
		"""
		if self.current_scene_id is not None:
			self.scene.exit_actor(actor)

		is_new_scene = scene_id not in self.scenes
		if is_new_scene:
			self.scenes[scene_id] = self.make_scene(scene_id)
			self.scenes[scene_id].generate(scene_id)
		if self.current_scene_id and self.scene.one_time():
			del self.scenes[self.current_scene_id]
		self.current_scene_id = scene_id
		self.scene.enter_actor(actor, passage)

		Log.debug("Finalizing dungeon...")
		self.update_vision(reset=is_new_scene)
		Log.debug("Dungeon is ready.")
	def generate(self, start_scene_id): # pragma: no cover
		""" Resets game and generates new state.
		Starts with given scene and places player (see make_player())
		at the default location (see Scene.enter_actor).
		Common pattern is create dummy Game object
		and then explicitly call generate().
		"""
		self.travel(self.make_player(), start_scene_id)
	def load(self, stream):
		""" Loads game data from the stream/state.
		"""
		self.playing_time = stream.read(int)
		self.rng = RNG(stream.read_int())
		self.current_scene_id = stream.read()

		self.scenes = {}
		while True:
			scene_id = stream.read()
			if not scene_id:
				break
			scene = self.make_scene(scene_id)
			scene.load(stream)
			self.scenes[scene_id] = scene
	def save(self, stream):
		""" Stores game data to the reader/state.
		"""
		stream.write(self.playing_time)
		stream.write(self.rng.value)
		stream.write(self.current_scene_id)
		for scene_id, scene in self.scenes.items():
			stream.write(scene_id)
			stream.write(scene)
		else:
			stream.write('')
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
	def update_vision(self, reset=False): # pragma: no cover
		""" Should update current vision field after disposition
		has changed (e.g. after movement or travelling).
		If reset is True, rebuild vision field from scratch
		(forgetting explored places).
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

	def attack(self, actor, other): # pragma: no cover
		""" Should perform attack on a hostile other actor
		and check consequences (death, loot etc).
		Also should address bump into the other actor if it is not hostile.
		"""
		raise NotImplementedError()
	def move_actor(self, actor, shift):
		""" Should move actor on scene by specified shift.
		"""
		Log.debug('Shift: {0}'.format(shift))
		actor_pos = self.scene.get_global_pos(actor)
		new_pos = actor_pos + shift
		if not self.scene.valid(new_pos):
			self.fire_event(Events.StareIntoVoid())
			return None

		other_actor = next((other for other in self.scene.iter_actors_at(new_pos, with_player=True) if other != actor), None)
		if other_actor:
			Log.debug('Actor at dest pos {0}: '.format(new_pos, other_actor))
			self.attack(actor, other_actor)
			return True

		if self.god.noclip:
			passable = True
		else:
			passable = self.scene.can_move(actor, new_pos)
		if not passable:
			self.fire_event(Events.BumpIntoTerrain(actor, new_pos))
			return None

		return new_pos

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
