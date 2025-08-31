import logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Size, Matrix
from clckwrkbdgr.pcg import RNG
from . import events
from . import scene, items, appliances
from . import auto

class GodMode:
	""" God mode options.
	- vision: see through everything, ignore FOV/transparency.
	- noclip: walk through everything, ignoring obstacles.
	"""
	def __init__(self):
		self.vision = False
		self.noclip = False
	def toggle_vision(self):
		self.vision = not self.vision
	def toggle_noclip(self):
		self.noclip = not self.noclip

class Events:
	class Welcome(events.Event):
		""" New game was generated. """
		FIELDS = ''
	class WelcomeBack(events.Event):
		""" Existing game was loaded. """
		FIELDS = ''
	class StareIntoVoid(events.Event):
		""" No movement past the edge of the world. """
		FIELDS = ''
	class BumpIntoTerrain(events.Event):
		""" Bumps into impenetrable obstacle. """
		FIELDS = 'actor target'
	class BumpIntoActor(events.Event):
		""" Bumps into non-hostile actor. """
		FIELDS = 'actor target'
	class Attack(events.ImportantEvent):
		""" Attack was performed. """
		FIELDS = 'actor target damage'
	class Health(events.Event):
		""" Health stat has been changed. """
		FIELDS = 'target diff'
	class Death(events.ImportantEvent):
		""" It's bleeding demised. """
		FIELDS = 'target'
	class DropItem(events.ImportantEvent):
		""" Drops something on the floor. """
		FIELDS = 'actor item'
	class Move(events.Event):
		""" Location is changed. """
		FIELDS = 'actor dest'
	class AutoStop(events.ImportantEvent):
		""" Cannot proceed with automatic actions
		because of list of reasons.
		"""
		FIELDS = 'reason'
	class Discover(events.ImportantEvent):
		""" Something new is discovered on the map! """
		FIELDS = 'obj'
	class NothingToPickUp(events.Event):
		""" Nothing to pick up here. """
		FIELDS = ''
	class InventoryIsFull(events.Event):
		""" No room in the inventory. """
		FIELDS = 'item'
	class GrabItem(events.ImportantEvent):
		""" Grabs something from the floor. """
		FIELDS = 'actor item'
	class ConsumeItem(events.ImportantEvent):
		""" Consumes consumable item. """
		FIELDS = 'actor item'
	class NotConsumable(events.Event):
		""" Item is not consumable. """
		FIELDS = 'item'
	class Wield(events.ImportantEvent):
		""" Equips item. """
		FIELDS = 'actor item'
	class Unwield(events.ImportantEvent):
		""" Unequips item. """
		FIELDS = 'actor item'
	class NotWielding(events.ImportantEvent):
		""" Wielding nothing, cannot unwield. """
		FIELDS = ''
	class Wear(events.Event):
		""" Equip item as armor. """
		FIELDS = 'actor item'
	class TakeOff(events.Event):
		""" Take off equipped armor. """
		FIELDS = 'actor item'
	class NotWearing(events.Event):
		""" Wearing nothing; cannot take off. """
		FIELDS = ''
	class NotWearable(events.Event):
		""" Cannot wear item. """
		FIELDS = 'item'
	class NeedKey(events.Event):
		""" Locked; needs a key type to unlock. """
		FIELDS = 'key'
	class Descend(events.ImportantEvent):
		""" Descended to another level. """
		FIELDS = 'actor'
	class Ascend(events.ImportantEvent):
		""" Ascended to another level. """
		FIELDS = 'actor'
	class CannotDescend(events.Event):
		""" Cannot descend from here. """
		FIELDS = 'pos'
	class CannotAscend(events.Event):
		""" Cannot ascend from here. """
		FIELDS = 'pos'
	class GodModeSwitched(events.Event):
		""" God Mode state has been switched. """
		FIELDS = 'name state'

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
	def jump_to(self, actor, new_pos):
		""" Transfers actor to a new position on the current map.
		Does not perform any passability checks.
		Does not spend action points.
		Recalculates vision.
		"""
		self.scene.transfer_actor(actor, new_pos)
		self.update_vision()
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
		if self.current_scene_id and self.scene.one_time(): # pragma: no cover -- TODO
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
		self.fire_event(Events.Welcome())
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

		self.fire_event(Events.WelcomeBack())
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
		""" Should perform any automovement activities (if currently enabled).
		Performs next step from auto-movement queue, if any and until available.
		Stops on important events.
		"""
		if self.automovement is True: # Pending stop from previous action.
			self.automovement = None
		if not self.automovement:
			return False
		Log.debug('Performing queued actions.')
		shift = self.automovement.next()
		if not shift:
			self.automovement = None
			return False
		self.move_actor(self.scene.get_player(), shift)
		if self.has_unprocessed_events(important_only=True):
			Log.debug('New events in FOV, aborting auto-moving mode.')
			self.automovement = True # Pending stop on the next check.
			return True
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
		Default implementation stops if there are important
		objects/happenings in the Vision.
		"""
		stoppers = list(self.vision.iter_important())
		if stoppers:
			self.fire_event(Events.AutoStop(stoppers))
			return True
		return False

	def affect_health(self, target, diff):
		""" Changes health of given target.
		Raises events for health change and death.
		Removes monsters from the main list, if health reaches zero.
		Drops loot, if any.
		"""
		diff = target.affect_health(diff)
		self.fire_event(Events.Health(target, diff))
		if not target.is_alive():
			self.fire_event(Events.Death(target))
			for item in self.scene.rip(target):
				self.fire_event(Events.DropItem(target, item))
			return False
		return True
	def attack(self, actor, other):
		""" Perform attack on a hostile other actor
		and check consequences (death, loot etc).
		If other actor is not considered hostile, just bumps.
		Any action spend AP.
		Returns True is actual attack happened.
		"""
		if not actor.is_hostile_to(other):
			actor.spend_action_points()
			self.fire_event(Events.BumpIntoActor(actor, other))
			return False
		damage = max(0, actor.get_attack_damage() - other.get_protection())
		self.fire_event(Events.Attack(actor, other, damage))
		self.affect_health(other, -damage)
		self.update_vision()
		actor.spend_action_points()
	def wait(self, actor):
		""" Wait in place and do nothing for a turn. """
		actor.spend_action_points()
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
	def drop_item(self, actor, item):
		""" Drops item from inventory on the floor (item is removed).
		Produces events.
		"""
		item = actor.drop(item)
		self.scene.drop_item(item)
		self.fire_event(Events.DropItem(actor, item.item))
		actor.spend_action_points()
	def suicide(self, actor):
		# No spending action points, because actor will be completely removed.
		self.affect_health(actor, -actor.hp)
	def grab_item_here(self, actor):
		""" Grabs topmost item at given cell and puts to the inventory.
		Checks inventory size.
		Produces events.
		Returns picked item in case of success, None otherwise.
		"""
		pos = self.scene.get_global_pos(actor)
		item = next(self.scene.iter_items_at(pos), None)
		if not item:
			self.fire_event(Events.NothingToPickUp())
			return None
		try:
			actor.grab(item)
			item = self.scene.take_item(items.ItemAtPos(pos, item))
			self.fire_event(Events.GrabItem(actor, item))
			actor.spend_action_points()
		except actor.InventoryFull:
			self.fire_event(Events.InventoryIsFull(item))
			return None
		return item
	def consume_item(self, actor, item):
		""" Consumes item from inventory (item is removed).
		Applies corresponding effects, if item has any.
		Produces events, including events from consuming item.
		"""
		try:
			events = actor.consume(item)
			actor.spend_action_points()
			self.fire_event(Events.ConsumeItem(actor, item))
			for event in events:
				self.fire_event(event)
		except actor.ItemNotFit as e:
			self.fire_event(Events.NotConsumable(item))
			return False
		return True
	def wield_item(self, actor, item):
		""" Actor equips item from inventory.
		Produces events.
		"""
		try:
			actor.wield(item)
		except actor.SlotIsTaken:
			old_item = actor.unwield()
			if old_item:
				self.fire_event(Events.Unwield(actor, old_item))
			actor.wield(item)
		actor.spend_action_points()
		self.fire_event(Events.Wield(actor, item))
	def unwield_item(self, actor):
		""" Actor unequips item and puts back to the inventory.
		Produces events.
		"""
		item = actor.unwield()
		if item:
			actor.spend_action_points()
			self.fire_event(Events.Unwield(actor, item))
		else:
			self.fire_event(Events.NotWielding())
	def wear_item(self, actor, item):
		try:
			actor.wear(item)
		except actor.ItemNotFit as e:
			self.fire_event(Events.NotWearable(item))
			return
		except actor.SlotIsTaken:
			old_item = actor.take_off()
			self.fire_event(Events.TakeOff(actor, old_item))
			actor.wear(item)
		actor.spend_action_points()
		self.fire_event(Events.Wear(actor, item))
	def take_off_item(self, actor):
		if not actor.wearing:
			self.fire_event(Events.NotWearing())
		else:
			item = actor.take_off()
			self.fire_event(Events.TakeOff(actor, item))
			actor.spend_action_points()
	def _use_passage(self, actor, level_passage, travel_event):
		""" Use level passage object. """
		try:
			level_id, connected_passage = level_passage.use(actor)
			self.travel(actor, level_id, connected_passage)
			actor.spend_action_points()
			self.fire_event(travel_event(actor))
			return True
		except level_passage.Locked as e:
			self.fire_event(Events.NeedKey(e.key_item_type))
			return False
	def descend(self, actor):
		""" Descends onto new level, when standing on unlocked exit passage.
		May generate new level.
		"""
		here = self.scene.get_global_pos(actor)
		stairs_here = next((obj for obj in self.scene.iter_appliances_at(here) if isinstance(obj, appliances.LevelPassage) and obj.can_go_down), None)
		if not stairs_here:
			self.fire_event(Events.CannotDescend(here))
			return False
		return self._use_passage(actor, stairs_here, Events.Descend)
	def ascend(self, actor):
		""" Ascends onto new level, when standing on unlocked exit passage.
		May generate new level.
		"""
		here = self.scene.get_global_pos(actor)
		stairs_here = next((obj for obj in self.scene.iter_appliances_at(here) if isinstance(obj, appliances.LevelPassage) and obj.can_go_up), None)
		if not stairs_here:
			self.fire_event(Events.CannotAscend(here))
			return False
		return self._use_passage(actor, stairs_here, Events.Ascend)

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
