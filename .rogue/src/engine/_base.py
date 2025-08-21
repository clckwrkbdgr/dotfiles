import logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Size, Matrix
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
	class Move(events.Event):
		""" Location is changed. """
		FIELDS = 'actor dest'
	class Discover(events.ImportantEvent):
		""" Something new is discovered on the map! """
		FIELDS = 'obj'

class Game(object):
	""" Main object for the game mechanics.
	"""
	def __init__(self, rng=None):
		""" Creates and initializes empty Game.
		Rng is either RNG object, or integer seed.
		If rng is not specified, current time() is used as seed.
		"""
		if rng is None:
			import time
			rng = int(time.time())
		if isinstance(rng, int):
			rng = RNG(rng)
		self.rng = rng
		self.playing_time = 0
		self.god = GodMode()
		self.events = []
		self.scenes = {}
		self.current_scene_id = None
		self.automovement = None
		self.visions = {}
	@property
	def scene(self):
		return self.scenes[self.current_scene_id]
	@property
	def vision(self):
		if self.current_scene_id not in self.visions:
			self.visions[self.current_scene_id] = self.scene.make_vision()
		return self.visions[self.current_scene_id]

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

		if scene_id not in self.scenes:
			self.scenes[scene_id] = self.make_scene(scene_id)
			self.scenes[scene_id].generate(scene_id)
		if self.current_scene_id and self.scene.one_time():
			del self.scenes[self.current_scene_id]
			del self.visions[self.current_scene_id]
		self.current_scene_id = scene_id
		self.scene.enter_actor(actor, passage)

		Log.debug("Finalizing dungeon...")
		self.update_vision()
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
		Updates vision after loading.
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

		self.visions = {}
		while True:
			scene_id = stream.read()
			if not scene_id:
				break
			vision = self.scenes[scene_id].make_vision()
			vision.load(stream)
			self.visions[scene_id] = vision

		self.update_vision()
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

		for scene_id, vision in self.visions.items():
			stream.write(scene_id)
			stream.write(vision)
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
			try:
				return events.Events.process(event, bind_self=bind_self)
			except events.Events.NotRegistered as e: # pragma: no cover
				Log.warning(e)
				return None
	def process_events(self, raw=False, bind_self=None):
		""" Iterates over accumulated events and processes them immediately,
		yielding results of the processing.
		Effectively removes each processed event.
		If raw is True, yields tuples of (raw callback, event object) instead of executing them.
		"""
		while self.has_unprocessed_events():
			yield self.process_next_event(raw=raw, bind_self=bind_self)

	# Display.

	def is_visible(self, pos):
		""" Should return True is position on map is visible to player.
		By default the whole map is visible.
		"""
		return self.god.vision or self.vision.is_visible(pos)
	def is_visited(self, pos):
		""" Should return True is position on map was visited by player.
		By default the whole map is considered visited and remembered.
		"""
		return self.vision.is_explored(pos)
	def update_vision(self): # pragma: no cover
		""" Should update current vision field after disposition
		has changed (e.g. after movement or travelling).
		"""
		if not self.scene.get_player():
			return
		for obj in self.vision.visit(self.scene.get_player()):
			self.fire_event(Events.Discover(obj))
	def tostring(self, view_rect, visited=True):
		""" Returns string representation of the viewport.
		If visited is False, ignores remembered locations
		and returns only currently visible cells.
		"""
		result = Matrix(view_rect.size, ' ')
		for pos, cell_info in self.scene.iter_cells(view_rect):
			result.set_cell(pos - view_rect.topleft, self.str_cell(pos, cell_info, visited=visited))
		return result.tostring()
	def str_cell(self, pos, cell_info=None, visited=True):
		""" Returns string representation of the cell at the pos
		(1-char sprite symbol).
		See .get_sprite()
		If visited is False, ignores remembered locations
		and returns only currently visible cells.
		"""
		result = self.get_sprite(pos, cell_info=cell_info, visited=visited)
		return result.sprite if result else ' '
	def get_sprite(self, pos, cell_info=None, visited=True):
		""" Returns topmost Sprite at the specified world pos.
		Additional cell info may be passed (see Scene.get_cell_info()).
		Considers Vision (visible/remembered places).
		If visited is False, ignores remembered locations
		and returns only currently visible cells.
		"""
		if cell_info is None:
			cell_info = self.scene.get_cell_info(pos)
		if self.is_visible(pos):
			return self.scene.get_sprite(pos, cell_info)
		if visited and self.is_visited(pos):
			cell, objects, items, monsters = cell_info
			if objects:
				return objects[-1].sprite
			elif cell and cell.remembered:
				return cell.remembered
		return None

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
		""" Moves monster into given direction (if possible).
		If there is a monster, performs .attack().
		If there is an obstacle (terrain), produces BumpIntoTerrain event.
		May produce all sorts of other events (including from attack()).
		Returns True, is movement succeeds, otherwise False.
		"""
		Log.debug('Shift: {0}'.format(shift))
		actor_pos = self.scene.get_global_pos(actor)
		new_pos = actor_pos + shift
		if not self.scene.valid(new_pos):
			self.fire_event(Events.StareIntoVoid())
			return False

		other_actor = next((other for other in self.scene.iter_actors_at(new_pos, with_player=True) if other != actor), None)
		if other_actor:
			Log.debug('Actor at dest pos {0}: '.format(new_pos, other_actor))
			self.attack(actor, other_actor)
			return False

		if self.god.noclip:
			passable = True
		else:
			passable = self.scene.can_move(actor, new_pos)
		if not passable:
			actor.spend_action_points()
			self.fire_event(Events.BumpIntoTerrain(actor, new_pos))
			return False

		Log.debug('Shift is valid, updating pos: {0}'.format(actor.pos))

		self.scene.transfer_actor(actor, new_pos)
		self.fire_event(Events.Move(actor, new_pos))
		actor.spend_action_points()

		if actor == self.scene.get_player():
			self.scene.recalibrate(new_pos, Size(actor.vision, actor.vision))
			self.update_vision()
		return True

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
