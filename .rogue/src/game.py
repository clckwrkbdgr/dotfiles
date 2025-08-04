from . import pcg
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr.math import Point, Direction, Matrix, Size, Rect
import logging
Log = logging.getLogger('rogue')
from .engine import items, actors, scene, appliances
from . import engine
from .engine.terrain import Terrain
from .engine.events import Event
import clckwrkbdgr.math
from clckwrkbdgr.collections import DocstringEnum as Enum

class Version(Enum):
	""" INITIAL
	PERSISTENT_RNG
	TERRAIN_TYPES
	MONSTERS
	MONSTER_BEHAVIOR
	ITEMS
	INVENTORY
	WIELDING
	"""

class DiscoverEvent(Event):
	""" Something new is discovered on the map! """
	FIELDS = 'obj'
class AttackEvent(Event):
	""" Attack was performed. """
	FIELDS = 'actor target'
class HealthEvent(Event):
	""" Health stat has been changed. """
	FIELDS = 'target diff'
class DeathEvent(Event):
	""" Someone's is no more. """
	FIELDS = 'target'
class MoveEvent(Event):
	""" Location is changed. """
	FIELDS = 'actor dest'
class DescendEvent(Event):
	""" Descended to another level. """
	FIELDS = 'actor'
class BumpEvent(Event):
	""" Bumps into impenetrable obstacle. """
	FIELDS = 'actor dest'
class GrabItemEvent(Event):
	""" Grabs something from the floor. """
	FIELDS = 'actor item'
class DropItemEvent(Event):
	""" Drops something on the floor. """
	FIELDS = 'actor item'
class ConsumeItemEvent(Event):
	""" Consumes consumable item. """
	FIELDS = 'actor item'
class NotConsumable(Event):
	""" Item is not consumable. """
	FIELDS = 'item'
class EquipItemEvent(Event):
	""" Equips item. """
	FIELDS = 'actor item'
class UnequipItemEvent(Event):
	""" Unequips item. """
	FIELDS = 'actor item'

class Player(actors.EquippedMonster):
	pass

class LevelExit(appliances.Appliance):
	pass

class Angry(actors.EquippedMonster):
	def act(self, game):
		closest = []
		for monster in game.scene.monsters:
			if not self.is_hostile_to(monster):
				continue
			closest.append((clckwrkbdgr.math.distance(self.pos, monster.pos), monster))
		if not closest: # pragma: no cover
			return
		_, player = sorted(closest)[0]

		if not player: # pragma: no cover
			return
		if clckwrkbdgr.math.distance(self.pos, player.pos) == 1:
			game.attack(self, player)
		elif clckwrkbdgr.math.distance(self.pos, player.pos) <= self.vision:
			is_transparent = lambda p: game.scene.is_transparent_to_monster(p, self)
			if clckwrkbdgr.math.algorithm.FieldOfView.in_line_of_sight(self.pos, player.pos, is_transparent):
				direction = Direction.from_points(self.pos, player.pos)
				game.move(self, direction)

class Inert(actors.EquippedMonster):
	def act(self, game):
		closest = []
		for monster in game.scene.monsters:
			if not self.is_hostile_to(monster):
				continue
			closest.append((clckwrkbdgr.math.distance(self.pos, monster.pos), monster))
		if not closest: # pragma: no cover
			return
		_, player = sorted(closest)[0]

		if not player: # pragma: no cover
			return
		if clckwrkbdgr.math.distance(self.pos, player.pos) == 1:
			game.attack(self, player)

class Pathfinder(clckwrkbdgr.math.algorithm.MatrixWave):
	def __init__(self, *args, **kwargs):
		if kwargs.get('visited'):
			self.visited = kwargs.get('visited')
			del kwargs['visited']
		super(Pathfinder, self).__init__(*args, **kwargs)
	@staticmethod
	def allow_movement_direction(strata, from_point, to_point):
		""" Returns True, if current map allows direct movement from point to point. """
		shift = to_point - from_point
		is_diagonal = abs(shift.x) + abs(shift.y) == 2
		if not is_diagonal:
			return True
		if not strata.cell(from_point).allow_diagonal:
			return False
		if not strata.cell(to_point).allow_diagonal:
			return False
		return True
	def is_passable(self, p, from_point):
		return self.matrix.cell(p).passable and self.visited.cell(p) and self.allow_movement_direction(self.matrix, from_point, p)

class Vision(object):
	def __init__(self):
		self.visited = None
		self.field_of_view = clckwrkbdgr.math.algorithm.FieldOfView(10)
		self.visible_monsters = []
		self.visible_items = []
	def load(self, reader):
		self.visited = reader.read_matrix(lambda c:c=='1')
	def save(self, writer):
		writer.write(self.visited)
	def update(self, monster, scene):
		""" Recalculates visibility/FOV for the player.
		May produce Discover events, if some objects come into vision.
		Remembers already seen objects.
		"""
		current_visible_monsters = []
		current_visible_items = []
		is_transparent = lambda p: scene.is_transparent_to_monster(p, monster)
		for p in self.field_of_view.update(
				monster.pos,
				is_transparent=is_transparent,
				):
			cell = scene.strata.cell(p)

			for monster in scene.iter_actors_at(p):
				if monster not in self.visible_monsters:
					yield monster
				current_visible_monsters.append(monster)

			for item in scene.iter_items_at(p):
				if item not in self.visible_items:
					yield item
				current_visible_items.append(item)

			if self.visited.cell(p):
				continue
			for appliance in scene.iter_appliances_at(p):
				yield appliance
			self.visited.set_cell(p, True)
		self.visible_monsters = current_visible_monsters
		self.visible_items = current_visible_items

class Scene(scene.Scene):
	def __init__(self):
		self.strata = None
		self.monsters = []
		self.items = []
		self.appliances = []
	def load(self, reader):
		super(Scene, self).load(reader)
		self.strata = reader.read_matrix(Terrain)
		if reader.version > Version.MONSTERS:
			self.monsters.extend(reader.read_list(actors.Actor))
		if reader.version > Version.ITEMS:
			self.items.extend(reader.read_list(items.ItemAtPos))
		self.appliances.extend(reader.read_list(appliances.ObjectAtPos))
	def save(self, writer):
		writer.write(self.strata)
		writer.write(self.monsters)
		writer.write(self.items)
		writer.write(self.appliances)
	def is_transparent_to_monster(self, p, monster):
		""" True if cell at position p is transparent/visible to a monster. """
		if not self.strata.valid(p):
			return False
		if not self.strata.cell(p).passable:
			return False
		if self.strata.cell(p).dark:
			if clckwrkbdgr.math.distance(monster.pos, p) >= 1:
				return False
		return True
	def iter_cells(self, view_rect):
		for y in range(view_rect.height):
			for x in range(view_rect.width):
				pos = Point(x, y)
				yield pos, self.get_cell_info(pos)
	def get_cell_info(self, pos):
		return (
				self.strata.cell(pos),
				list(self.iter_appliances_at(pos)),
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)
	def get_player(self):
		""" Returns player character if exists, or None. """
		return next((monster for monster in self.monsters if isinstance(monster, Player)), None)
	def iter_actors_at(self, pos, with_player=False):
		""" Yield all monsters at given cell. """
		for monster in self.monsters:
			if not with_player and isinstance(monster, Player):
				continue
			if monster.pos == pos:
				yield monster
	def iter_items_at(self, pos):
		""" Return all items at given cell. """
		for item_pos, item in self.items:
			if item_pos == pos:
				yield item
	def iter_appliances_at(self, pos):
		for obj_pos, obj in self.appliances:
			if obj_pos == pos:
				yield obj

class Game(engine.Game):
	""" Main game object.

	Override definitions for content:
	- BUILDERS: list of Builder classes to build maps.
	- SETTLERS: list of Settler classes to populate them.
	- TERRAIN: dict, registry of Terrain classes by their IDs used in Builders.
	- SPECIES: dict, registry of Species classes by their IDs used in Settlers.
	- ITEMS: dict, registry of Item classes by their IDs used in Settlers.
	"""

	class AutoMovementStopped(BaseException):
		""" Raised when current automovement mode was stopped. """
		pass

	BUILDERS = None
	SETTLERS = None
	TERRAIN = None
	SPECIES = None
	ITEMS = None

	def __init__(self, rng_seed=None, builders=None):
		""" Creates game instance and optionally generate new world.
		Custom rng_seed may be used for PCG.
		If dummy = True, does not automatically generate or load game, just create empty object.
		Optional builders/settlers may be passed to override default class variables.
		If load_from_reader is given, it should be a Reader class, from which game is loaded.
		Otherwise new game is generated.
		"""
		super(Game, self).__init__(rng=RNG(rng_seed))
		self.builders = builders or self.BUILDERS
		assert not hasattr(self, 'SETTLERS') or self.SETTLERS is None
		self.god = God()
		self.autoexploring = False
		self.movement_queue = []
		self.scene = Scene()
		self.vision = Vision()
	def generate(self):
		self.build_new_strata()
	def load(self, reader):
		""" Loads game from reader. """
		if reader.version > Version.PERSISTENT_RNG:
			self.rng = RNG(reader.read_int())

		self.scene.load(reader)
		self.vision.load(reader)

		if self.scene.get_player(): # pragma: no cover
			for obj in self.vision.update(self.scene.get_player(), self.scene):
				self.fire_event(DiscoverEvent(obj))
		Log.debug('Loaded.')
		Log.debug(repr(self.scene.strata))
		Log.debug('Player: {0}'.format(self.scene.get_player()))
	def save(self, writer):
		""" Saves game using writer. """
		writer.write(self.rng.value)
		writer.write(self.scene)
		self.vision.save(writer)
	def is_finished(self):
		return not (self.scene.get_player() and self.scene.get_player().is_alive())
	def end_turn(self):
		if self.scene.get_player():
			self.scene.get_player().spend_action_points()
	def process_others(self):
		if self.scene.get_player() and self.scene.get_player().has_acted():
			for monster in self.scene.monsters:
				if isinstance(monster, Player):
					continue
				monster.act(self)
			if self.scene.get_player():
				self.scene.get_player().add_action_points()
	def stop_automovement(self):
		try:
			self.autostop()
		except Game.AutoMovementStopped:
			pass
	def suicide(self, monster):
		self.affect_health(monster, -monster.hp)
	def toggle_god_vision(self):
		self.god.vision = not self.god.vision
	def toggle_god_noclip(self):
		self.god.noclip = not self.god.noclip
	def wait(self):
		pass
	def get_viewport(self):
		""" Returns current viewport rect. """
		return Rect(Point(0, 0), self.scene.strata.size)
	def is_visible(self, pos):
		return self.god.vision or self.vision.field_of_view.is_visible(pos.x, pos.y)
	def is_visited(self, pos):
		return self.vision.visited.cell(pos)
	def tostring(self, with_fov=False):
		""" Creates string representation of the current viewport.
		If with_fov=True, considers transparency/lighting, otherwise everything is visible.
		If strcell is given, it is lambda that takes pair (x, y) and returns single-char representation of that cell. By default get_sprite(x, y) is used.
		"""
		if not with_fov:
			return self.scene.tostring(self.get_viewport())
		result = Matrix(self.get_viewport().size)
		for pos, cell_info in self.scene.iter_cells(self.get_viewport()):
			result.set_cell(pos, self.get_cell_repr(pos, cell_info) or ' ')
		return result.tostring()
	def get_cell_repr(self, pos, cell_info):
		cell, objects, items, monsters = cell_info
		if self.vision.field_of_view.is_visible(pos.x, pos.y):
			if monsters:
				return monsters[-1].sprite.sprite
			if items:
				return items[-1].sprite.sprite
			if objects:
				return objects[-1].sprite.sprite
			return cell.sprite.sprite
		if objects and self.vision.visited.cell(pos):
			return objects[-1].sprite.sprite
		if self.vision.visited.cell(pos) and cell.remembered:
			return cell.remembered.sprite
		return None
	def build_new_strata(self):
		""" Constructs and populates new random level.
		Transfers player from previous level.
		Updates vision afterwards.
		"""
		builder = self.rng.choice(self.builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		Log.debug('With RNG: {0}...'.format(self.rng.value))
		builder = builder(self.rng, Size(80, 23))
		settler = builder
		Log.debug("Populating dungeon: {0}".format(settler))
		builder.generate()
		self.scene.strata = builder.make_grid()
		self.vision.visited = Matrix(self.scene.strata.size, False)

		appliances = list(builder.make_appliances())
		start_pos = next(_pos for _pos, _name in appliances if _name == 'start')
		self.scene.appliances = [_entry for _entry in appliances if _entry.obj != 'start']
		player = self.scene.get_player()
		if player:
			player.pos = start_pos
		else:
			player = self.SPECIES['Player'](start_pos)
			player.fill_drops(self.rng)
		self.scene.monsters[:] = [player]
		for monster in settler.make_actors():
			monster.fill_drops(self.rng)
			self.scene.monsters.append(monster)
		self.scene.items[:] = []
		for item in settler.make_items():
			self.scene.items.append(item)

		Log.debug("Finalizing dungeon...")
		for obj in self.vision.update(self.scene.get_player(), self.scene):
			self.fire_event(DiscoverEvent(obj))
		Log.debug("Dungeon is ready.")
	def move(self, actor, direction):
		""" Moves monster into given direction (if possible).
		If there is a monster, performs attack().
		May produce all sorts of other events.
		Returns True, is action succeeds, otherwise False.
		"""
		shift = direction
		Log.debug('Shift: {0}'.format(shift))
		new_pos = actor.pos + shift
		if not self.scene.strata.valid(new_pos):
			return False
		if self.god.noclip:
			passable = True
		else:
			passable = self.scene.strata.cell(new_pos).passable
		if not passable:
			self.fire_event(BumpEvent(actor, new_pos))
			return False
		if not Pathfinder.allow_movement_direction(self.scene.strata, actor.pos, new_pos):
			self.fire_event(BumpEvent(actor, new_pos))
			return False
		monster = next(self.scene.iter_actors_at(new_pos), None)
		if monster:
			Log.debug('Monster at dest pos {0}: '.format(new_pos, monster))
			self.attack(actor, monster)
			return True
		Log.debug('Shift is valid, updating pos: {0}'.format(actor.pos))
		self.fire_event(MoveEvent(actor, new_pos))
		actor.pos = new_pos
		for obj in self.vision.update(self.scene.get_player(), self.scene):
			self.fire_event(DiscoverEvent(obj))
		return True
	def affect_health(self, target, diff):
		""" Changes health of given target.
		Removes monsters from the main list, if health is zero.
		Raises events for health change and death.
		"""
		diff = target.affect_health(diff)
		self.fire_event(HealthEvent(target, diff))
		self.check_alive(target)
	def check_alive(self, target):
		if not target.is_alive():
			self.fire_event(DeathEvent(target))
			for item in target.drop_all():
				self.scene.items.append(item)
				self.vision.visible_items.append(item.item)
				self.fire_event(DropItemEvent(target, item.item))
			self.scene.monsters.remove(target)
	def attack(self, actor, target):
		""" Attacks target monster.
		Raises attack event.
		"""
		self.fire_event(AttackEvent(actor, target))
		damage = max(0, actor.get_attack_damage() - target.get_protection())
		self.affect_health(target, -damage)
		if self.get_player():
			for obj in self.vision.update(self.scene.get_player(), self.scene): # pragma: no cover -- TODO
				self.fire_event(DiscoverEvent(obj))
	def grab_item_at(self, actor, pos):
		""" Grabs topmost item at given cell and puts to the inventory.
		Produces events.
		"""
		item = next(self.scene.iter_items_at(pos), None)
		if not item:
			return
		self.fire_event(GrabItemEvent(actor, item))
		self.scene.items.remove(item)
		actor.grab(item)
	def consume_item(self, monster, item):
		""" Consumes item from inventory (item is removed).
		Applies corresponding effects, if item has any.
		Produces events.
		"""
		try:
			events = monster.consume(item)
		except monster.ItemNotFit as e:
			self.fire_event(NotConsumable(item))
			return
		self.fire_event(ConsumeItemEvent(monster, item))
		for event in events:
			self.fire_event(event)
		self.check_alive(monster)
	def drop_item(self, monster, item):
		""" Drops item from inventory (item is removed).
		Produces events.
		"""
		item = monster.drop(item)
		self.scene.items.append(item)
		self.vision.visible_items.append(item.item)
		self.fire_event(DropItemEvent(monster, item.item))
	def wield_item(self, monster, item):
		""" Monster equips item from inventory.
		Produces events.
		"""
		try:
			monster.wield(item)
		except monster.SlotIsTaken:
			old_item = monster.unwield()
			if old_item:
				self.fire_event(UnequipItemEvent(monster, old_item))
			monster.wield(item)
		self.fire_event(EquipItemEvent(monster, item))
	def unwield_item(self, monster):
		""" Monster unequips item and puts back to the inventory.
		Produces events.
		"""
		item = monster.unwield()
		if item:
			self.fire_event(UnequipItemEvent(monster, item))
	def jump_to(self, new_pos):
		""" Teleports player to new pos. """
		self.scene.get_player().pos = new_pos
		for obj in self.vision.update(self.scene.get_player(), self.scene):
			self.fire_event(DiscoverEvent(obj))
	def descend(self):
		""" Descends onto new level, when standing on exit pos.
		Generates new level.
		Otherwise does nothing.
		"""
		for obj in self.scene.iter_appliances_at(self.scene.get_player().pos):
			if isinstance(obj, LevelExit):
				self.fire_event(DescendEvent(self.scene.get_player()))
				self.build_new_strata()
				break
	def find_path(self, start, find_target):
		""" Find free path from start and until find_target() returns suitable target.
		Otherwise return None.
		"""
		wave = Pathfinder(self.scene.strata, visited=self.vision.visited)
		path = wave.run(start, find_target)
		if not path:
			return None
		if path[0] == self.scene.get_player().pos: # We're already standing there.
			path.pop(0)
		return path
	def automove(self, dest=None):
		if self.vision.visible_monsters:
			self.fire_event(DiscoverEvent('monsters'))
			return
		if dest is None:
			path = self._start_autoexploring()
		else:
			path = self._walk_to(dest)
		if path:
			self.movement_queue.extend(path)
		return bool(path)
	def _walk_to(self, dest):
		""" Starts auto-walking towards dest, if possible.
		Does not start when monsters are around and produces event.
		"""
		path = self.find_path(self.scene.get_player().pos,
				find_target=lambda wave: dest if dest in wave else None,
				)
		return path
	def _start_autoexploring(self):
		""" Starts auto-exploring, if there are unknown places.
		Does not start when monsters are around and produces event.
		"""
		path = self.find_path(self.scene.get_player().pos,
			find_target=lambda wave: next((target for target in sorted(wave)
			if any(
				not self.vision.visited.cell(p)
				for p in clckwrkbdgr.math.get_neighbours(self.scene.strata, target, with_diagonal=True)
				)
			), None),
			)
		self.autoexploring = bool(path)
		return path
	def in_automovement(self):
		return self.autoexploring or bool(self.movement_queue)
	def perform_automovement(self):
		try:
			self.perform_automovement_step()
		except Game.AutoMovementStopped:
			pass
		return True
	def perform_automovement_step(self):
		""" Performs next step from auto-movement queue, if any.
		Stops on events.
		"""
		if not self.movement_queue:
			return False
		if self.has_unprocessed_events():
			Log.debug('New events in FOV, aborting auto-moving mode.')
			return self.autostop()
		Log.debug('Performing queued actions.')
		new_pos = self.movement_queue.pop(0)
		self.jump_to(new_pos)
		if self.movement_queue:
			return True
		if self.autoexploring:
			if not self.automove():
				self.autoexploring = False
				raise Game.AutoMovementStopped()
		else:
			raise Game.AutoMovementStopped()
		return True
	def autostop(self):
		""" Stops and resets auto-movement. """
		self.movement_queue[:] = []
		self.autoexploring = False
		raise Game.AutoMovementStopped()

class God:
	""" God mode options.
	- vision: see through everything, ignore FOV/transparency.
	- noclip: walk through everything, ignoring obstacles.
	"""
	def __init__(self):
		self.vision = False
		self.noclip = False
