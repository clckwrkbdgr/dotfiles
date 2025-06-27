from .defs import *
from . import pcg
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr.math import Point, Direction, Matrix, Size, Rect
import logging
Log = logging.getLogger('rogue')
from .defs import Action
from . import monsters, items, terrain
from . import engine
from .engine.events import Event
import clckwrkbdgr.math

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
class EquipItemEvent(Event):
	""" Equips item. """
	FIELDS = 'actor item'
class UnequipItemEvent(Event):
	""" Unequips item. """
	FIELDS = 'actor item'

class Pathfinder(clckwrkbdgr.math.algorithm.MatrixWave):
	@staticmethod
	def allow_movement_direction(strata, from_point, to_point):
		""" Returns True, if current map allows direct movement from point to point. """
		shift = to_point - from_point
		is_diagonal = abs(shift.x) + abs(shift.y) == 2
		if not is_diagonal:
			return True
		if not strata.cell(from_point).terrain.allow_diagonal:
			return False
		if not strata.cell(to_point).terrain.allow_diagonal:
			return False
		return True
	def is_passable(self, p, from_point):
		return self.matrix.cell(p).terrain.passable and self.matrix.cell(p).visited and self.allow_movement_direction(self.matrix, from_point, p)

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
		self.field_of_view = clckwrkbdgr.math.algorithm.FieldOfView(10)
		self.autoexploring = False
		self.movement_queue = []
		self.monsters = []
		self.items = []
		self.visible_monsters = []
		self.visible_items = []
		self.player_turn = True
	def generate(self):
		self.build_new_strata()
	def load(self, reader):
		""" Loads game from reader. """
		if reader.version > Version.PERSISTENT_RNG:
			self.rng = RNG(reader.read_int())

		legacy_player = None
		if reader.version <= Version.MONSTERS:
			legacy_player = monsters.Monster(self.SPECIES['player'], monsters.Behavior.PLAYER, reader.read_point())
		self.exit_pos = reader.read_point()
		self.remembered_exit = reader.read_bool()

		reader.set_meta_info('ITEMS', self.ITEMS)
		reader.set_meta_info('SPECIES', self.SPECIES)
		reader.set_meta_info('TERRAIN', self.TERRAIN)
		self.strata = reader.read_matrix(terrain.Cell)
		if legacy_player:
			self.monsters.append(legacy_player)
		if reader.version > Version.MONSTERS:
			self.monsters.extend(reader.read_list(monsters.Monster))
		if reader.version > Version.ITEMS:
			self.items.extend(reader.read_list(items.Item))

		self.update_vision()
		Log.debug('Loaded.')
		Log.debug(repr(self.strata))
		Log.debug('Player: {0}'.format(self.get_player()))
	def save(self, writer):
		""" Saves game using writer. """
		writer.write(self.rng.value)
		writer.write(self.exit_pos)
		writer.write(self.remembered_exit)
		writer.write(self.strata)
		writer.write(self.monsters)
		writer.write(self.items)
	def is_finished(self):
		return not (self.get_player() and self.get_player().is_alive())
	def _pre_action(self):
		if not self.get_player():
			return False
		try:
			self.perform_automovement()
		except Game.AutoMovementStopped:
			pass
		return True
	def end_turn(self):
		self.player_turn = False
		if not self.player_turn:
			for monster in self.monsters:
				if monster.behavior == monsters.Behavior.PLAYER:
					continue
				self._perform_monster_actions(monster)
			self.player_turn = True
	def autostop(self):
		try:
			self.stop_automovement()
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
	def _perform_monster_actions(self, monster):
		""" Controller for monster actions (depends on behavior). """
		if monster.behavior == monsters.Behavior.DUMMY:
			pass
		elif monster.behavior == monsters.Behavior.INERT:
			if self.get_player():
				if clckwrkbdgr.math.distance(monster.pos, self.get_player().pos) == 1:
					self.attack(monster, self.get_player())
		elif monster.behavior == monsters.Behavior.ANGRY:
			if self.get_player():
				if clckwrkbdgr.math.distance(monster.pos, self.get_player().pos) == 1:
					self.attack(monster, self.get_player())
				elif clckwrkbdgr.math.distance(monster.pos, self.get_player().pos) <= monster.species.vision:
					is_transparent = lambda p: self.is_transparent_to_monster(p, monster)
					if clckwrkbdgr.math.algorithm.FieldOfView.in_line_of_sight(monster.pos, self.get_player().pos, is_transparent):
						direction = Direction.from_points(monster.pos, self.get_player().pos)
						self.move(monster, direction)
	def get_viewport(self):
		""" Returns current viewport size (for UI purposes). """
		return self.strata.size
	def tostring(self, with_fov=False):
		""" Creates string representation of the current viewport.
		If with_fov=True, considers transparency/lighting, otherwise everything is visible.
		If strcell is given, it is lambda that takes pair (x, y) and returns single-char representation of that cell. By default get_sprite(x, y) is used.
		"""
		if not with_fov:
			old_god_vision = self.god.vision
			self.god.vision = True
		result = Matrix(self.get_viewport())
		for pos, cell_info in self.iter_cells(Rect(Point(0, 0), self.get_viewport())):
			result.set_cell(pos, self.get_cell_repr(pos, cell_info) or ' ')
		if not with_fov:
			self.god.vision = old_god_vision
		return result.tostring()
	def iter_cells(self, view_rect):
		for y in range(view_rect.height):
			for x in range(view_rect.width):
				pos = Point(x, y)
				yield pos, self.get_cell_info(pos)
	def get_cell_info(self, pos):
		return (
				self.strata.cell(pos),
				list(self.iter_placements_at(pos)),
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)
	def get_cell_repr(self, pos, cell_info):
		cell, objects, items, monsters = cell_info
		if self.god.vision or self.field_of_view.is_visible(pos.x, pos.y):
			if monsters:
				return monsters[-1].species.sprite
			if items:
				return items[-1].item_type.sprite
			if objects:
				return '>'
			return cell.terrain.sprite
		if objects:
			if self.remembered_exit:
				return '>'
		if cell.visited and cell.terrain.remembered:
			return cell.terrain.remembered
		return None
	def is_transparent_to_monster(self, p, monster):
		""" True if cell at position p is transparent/visible to a monster. """
		if not self.strata.valid(p):
			return False
		if not self.strata.cell(p).terrain.passable:
			return False
		if self.strata.cell(p).terrain.dark:
			if clckwrkbdgr.math.distance(monster.pos, p) >= 1:
				return False
		return True
	def update_vision(self):
		""" Recalculates visibility/FOV for the player.
		May produce Discover events, if some objects come into vision.
		Remembers already seen objects.
		"""
		if not self.get_player():
			return
		current_visible_monsters = []
		current_visible_items = []
		is_transparent = lambda p: self.is_transparent_to_monster(p, self.get_player())
		for p in self.field_of_view.update(
				self.get_player().pos,
				is_transparent=is_transparent,
				):
			cell = self.strata.cell(p)

			for monster in self.iter_actors_at(p):
				if monster not in self.visible_monsters:
					self.fire_event(DiscoverEvent(monster))
				current_visible_monsters.append(monster)

			for item in self.iter_items_at(p):
				if item not in self.visible_items:
					self.fire_event(DiscoverEvent(item))
				current_visible_items.append(item)

			if cell.visited:
				continue
			for placement in self.iter_placements_at(p):
				self.fire_event(DiscoverEvent(placement))
			cell.visited = True
		self.visible_monsters = current_visible_monsters
		self.visible_items = current_visible_items
		if self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
			self.remembered_exit = True
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
		self.strata = builder.make_grid()

		appliances = list(builder.make_appliances())
		start_pos = next(_pos for _pos, _name in appliances if _name == 'start')
		player = self.get_player()
		if player:
			player.pos = start_pos
		else:
			player = monsters.Monster(self.SPECIES['player'], monsters.Behavior.PLAYER, start_pos)
			player.fill_inventory_from_drops(self.rng, self.ITEMS)
		self.monsters[:] = [player]
		for monster in settler.make_actors():
			monster.fill_inventory_from_drops(self.rng, self.ITEMS)
			self.monsters.append(monster)
		self.items[:] = []
		for item in settler.make_items():
			self.items.append(item)

		Log.debug("Finalizing dungeon...")
		self.exit_pos = next(_pos for _pos, _name in appliances if _name == 'exit')
		self.remembered_exit = False
		self.update_vision()
		Log.debug("Dungeon is ready.")
	def get_player(self):
		""" Returns player character if exists, or None. """
		return next((monster for monster in self.monsters if monster.behavior == monsters.Behavior.PLAYER), None)
	def move(self, actor, direction):
		""" Moves monster into given direction (if possible).
		If there is a monster, performs attack().
		May produce all sorts of other events.
		Returns True, is action succeeds, otherwise False.
		"""
		shift = direction
		Log.debug('Shift: {0}'.format(shift))
		new_pos = actor.pos + shift
		if not self.strata.valid(new_pos):
			return False
		if self.god.noclip:
			passable = True
		else:
			passable = self.strata.cell(new_pos).terrain.passable
		if not passable:
			self.fire_event(BumpEvent(actor, new_pos))
			return False
		if not Pathfinder.allow_movement_direction(self.strata, actor.pos, new_pos):
			self.fire_event(BumpEvent(actor, new_pos))
			return False
		monster = next(self.iter_actors_at(new_pos), None)
		if monster:
			Log.debug('Monster at dest pos {0}: '.format(new_pos, monster))
			self.attack(actor, monster)
			return True
		Log.debug('Shift is valid, updating pos: {0}'.format(actor.pos))
		self.fire_event(MoveEvent(actor, new_pos))
		actor.pos = new_pos
		self.update_vision()
		return True
	def affect_health(self, target, diff):
		""" Changes health of given target.
		Removes monsters from the main list, if health is zero.
		Raises events for health change and death.
		"""
		new_hp = target.hp + diff
		if new_hp < 0:
			new_hp = 0
			diff = new_hp - target.hp
		elif new_hp >= target.species.max_hp:
			new_hp = target.species.max_hp
			diff = new_hp - target.hp
		target.hp += diff
		self.fire_event(HealthEvent(target, diff))
		if not target.is_alive():
			self.fire_event(DeathEvent(target))
			drops = target.drop_loot()
			for item in drops:
				self.drop_item(target, item)
			self.monsters.remove(target)
	def attack(self, actor, target):
		""" Attacks target monster.
		Raises attack event.
		"""
		self.fire_event(AttackEvent(actor, target))
		self.affect_health(target, -1)
		self.update_vision()
	def iter_actors_at(self, pos, with_player=False):
		""" Yield all monsters at given cell. """
		for monster in self.monsters:
			if not with_player and monster.behavior == monsters.Behavior.PLAYER:
				continue
			if monster.pos == pos:
				yield monster
	def iter_items_at(self, pos):
		""" Return all items at given cell. """
		for item in self.items:
			if item.pos == pos:
				yield item
	def iter_placements_at(self, pos):
		if self.exit_pos == pos:
			yield '>'
	def grab_item_at(self, actor, pos):
		""" Grabs topmost item at given cell and puts to the inventory.
		Produces events.
		"""
		item = next(self.iter_items_at(pos), None)
		if not item:
			return
		self.fire_event(GrabItemEvent(actor, item))
		self.items.remove(item)
		actor.inventory.append(item)
	def consume_item(self, monster, item):
		""" Consumes item from inventory (item is removed).
		Applies corresponding effects, if item has any.
		Produces events.
		"""
		assert item in monster.inventory
		monster.inventory.remove(item)
		self.fire_event(ConsumeItemEvent(monster, item))
		if item.item_type.effect == items.Effect.HEALING:
			self.affect_health(monster, +5)
	def drop_item(self, monster, item):
		""" Drops item from inventory (item is removed).
		Produces events.
		"""
		assert item in monster.inventory
		item.pos = monster.pos
		monster.inventory.remove(item)
		self.items.append(item)
		self.visible_items.append(item)
		self.fire_event(DropItemEvent(monster, item))
	def wield_item(self, monster, item):
		""" Monster equips item from inventory.
		Produces events.
		"""
		assert item in monster.inventory
		if monster.wielding:
			self.unwield_item(monster)
		monster.inventory.remove(item)
		monster.wielding = item
		self.fire_event(EquipItemEvent(monster, item))
	def unwield_item(self, monster):
		""" Monster unequips item and puts back to the inventory.
		Produces events.
		"""
		if not monster.wielding:
			return
		item = monster.wielding
		monster.inventory.append(item)
		monster.wielding = None
		self.fire_event(UnequipItemEvent(monster, item))
	def jump_to(self, new_pos):
		""" Teleports player to new pos. """
		self.get_player().pos = new_pos
		self.update_vision()
	def descend(self):
		""" Descends onto new level, when standing on exit pos.
		Generates new level.
		Otherwise does nothing.
		"""
		if self.get_player().pos != self.exit_pos:
			return
		self.fire_event(DescendEvent(self.get_player()))
		self.build_new_strata()
	def find_path(self, start, find_target):
		""" Find free path from start and until find_target() returns suitable target.
		Otherwise return None.
		"""
		wave = Pathfinder(self.strata)
		path = wave.run(start, find_target)
		if not path:
			return None
		if path[0] == self.get_player().pos: # We're already standing there.
			path.pop(0)
		return path
	def walk_to(self, dest):
		""" Starts auto-walking towards dest, if possible.
		Does not start when monsters are around and produces event.
		"""
		if self.visible_monsters:
			self.fire_event(DiscoverEvent('monsters'))
			return
		path = self.find_path(self.get_player().pos,
				find_target=lambda wave: dest if dest in wave else None,
				)
		if path:
			self.movement_queue.extend(path)
	def start_autoexploring(self):
		""" Starts auto-exploring, if there are unknown places.
		Does not start when monsters are around and produces event.
		"""
		if self.visible_monsters:
			self.fire_event(DiscoverEvent('monsters'))
			return False
		path = self.find_path(self.get_player().pos,
			find_target=lambda wave: next((target for target in sorted(wave)
			if any(
				not self.strata.cell(p).visited
				for p in clckwrkbdgr.math.get_neighbours(self.strata, target, with_diagonal=True)
				)
			), None),
			)
		if not path:
			return False
		self.movement_queue.extend(path)
		self.autoexploring = True
		return True
	def in_automovement(self):
		return self.autoexploring or bool(self.movement_queue)
	def perform_automovement(self):
		""" Performs next step from auto-movement queue, if any.
		Stops on events.
		"""
		if not self.movement_queue:
			return False
		if self.has_unprocessed_events():
			Log.debug('New events in FOV, aborting auto-moving mode.')
			return self.stop_automovement()
		Log.debug('Performing queued actions.')
		new_pos = self.movement_queue.pop(0)
		self.jump_to(new_pos)
		if self.movement_queue:
			return True
		if self.autoexploring:
			if not self.start_autoexploring():
				self.autoexploring = False
				raise Game.AutoMovementStopped()
		else:
			raise Game.AutoMovementStopped()
		return True
	def stop_automovement(self):
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
