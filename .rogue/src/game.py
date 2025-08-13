from . import pcg
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr.math import Point, Direction, Matrix, Size, Rect
import logging
Log = logging.getLogger('rogue')
from .engine import items, actors, scene, appliances
from . import engine
from .engine import auto
from .engine import math
from .engine.terrain import Terrain
from .engine.events import Event, ImportantEvent
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

class DiscoverEvent(ImportantEvent):
	""" Something new is discovered on the map! """
	FIELDS = 'obj'
class AttackEvent(ImportantEvent):
	""" Attack was performed. """
	FIELDS = 'actor target'
class HealthEvent(Event):
	""" Health stat has been changed. """
	FIELDS = 'target diff'
class DeathEvent(ImportantEvent):
	""" Someone's is no more. """
	FIELDS = 'target'
class MoveEvent(Event):
	""" Location is changed. """
	FIELDS = 'actor dest'
class DescendEvent(ImportantEvent):
	""" Descended to another level. """
	FIELDS = 'actor'
class BumpEvent(Event):
	""" Bumps into impenetrable obstacle. """
	FIELDS = 'actor dest'
class GrabItemEvent(ImportantEvent):
	""" Grabs something from the floor. """
	FIELDS = 'actor item'
class DropItemEvent(ImportantEvent):
	""" Drops something on the floor. """
	FIELDS = 'actor item'
class ConsumeItemEvent(ImportantEvent):
	""" Consumes consumable item. """
	FIELDS = 'actor item'
class NotConsumable(Event):
	""" Item is not consumable. """
	FIELDS = 'item'
class EquipItemEvent(ImportantEvent):
	""" Equips item. """
	FIELDS = 'actor item'
class UnequipItemEvent(ImportantEvent):
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
				game.move_actor(self, direction)

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

class Vision(math.Vision):
	def __init__(self):
		self.visited = None
		self.field_of_view = clckwrkbdgr.math.algorithm.FieldOfView(10)
		self.visible_monsters = []
		self.visible_items = []
	def load(self, reader):
		self.visited = reader.read_matrix(lambda c:c=='1')
	def save(self, writer):
		writer.write(self.visited)
	def is_explored(self, pos):
		return self.visited.cell(pos)
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
	def __init__(self, rng, builders):
		self.rng = rng
		self.builders = builders
		self.strata = None
		self.monsters = []
		self.items = []
		self.appliances = []
	def generate(self, id):
		builder = self.rng.choice(self.builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		Log.debug('With RNG: {0}...'.format(self.rng.value))
		builder = builder(self.rng, Size(80, 23))
		settler = builder
		Log.debug("Populating dungeon: {0}".format(settler))
		builder.generate()

		self.strata = builder.make_grid()

		appliances = list(builder.make_appliances())
		self._start_pos = next(_pos for _pos, _name in appliances if _name == 'start')
		self.appliances = [_entry for _entry in appliances if _entry.obj != 'start']
		for monster in settler.make_actors():
			monster.fill_drops(self.rng)
			self.monsters.append(monster)
		for item in settler.make_items():
			self.items.append(item)
	def exit_actor(self, actor):
		self.monsters.remove(actor)
		return actor
	def enter_actor(self, actor, location):
		actor.pos = self._start_pos
		self.monsters.insert(0, actor)
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
	def valid(self, pos): # pragma: no cover -- TODO
		return self.strata.valid(pos)
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
	def iter_active_monsters(self):
		return self.monsters

class Game(engine.Game):
	""" Main game object.

	Override definitions for content:
	- BUILDERS: list of Builder classes to build maps.
	"""

	BUILDERS = None
	PLAYER_CLASS = None

	def __init__(self, rng_seed=None):
		""" Creates game instance and optionally generate new world.
		Custom rng_seed may be used for PCG.
		If dummy = True, does not automatically generate or load game, just create empty object.
		Optional builders/settlers may be passed to override default class variables.
		If load_from_reader is given, it should be a Reader class, from which game is loaded.
		Otherwise new game is generated.
		"""
		super(Game, self).__init__(rng=RNG(rng_seed))
		self.vision = Vision()
	def generate(self):
		self.scene = Scene(self.rng, self.BUILDERS)
		self.build_new_strata()
	def load(self, reader):
		""" Loads game from reader. """
		if reader.version > Version.PERSISTENT_RNG:
			self.rng = RNG(reader.read_int())

		self.scene = Scene(self.rng, self.BUILDERS)
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
	def end_turn(self):
		if self.scene.get_player():
			self.scene.get_player().spend_action_points()
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
	def make_player(self):
		player = self.PLAYER_CLASS(None)
		player.fill_drops(self.rng)
		return player
	def build_new_strata(self):
		""" Constructs and populates new random level.
		Transfers player from previous level.
		Updates vision afterwards.
		"""
		player = self.scene.get_player()
		if player:
			self.scene.exit_actor(player)
		else:
			player = self.make_player()

		self.scene = Scene(self.rng, self.scene.builders)
		self.scene.generate(None)
		self.scene.enter_actor(player, None)

		Log.debug("Finalizing dungeon...")
		self.vision.visited = Matrix(self.scene.strata.size, False)
		for obj in self.vision.update(self.scene.get_player(), self.scene):
			self.fire_event(DiscoverEvent(obj))
		Log.debug("Dungeon is ready.")
	def move_actor(self, actor, direction):
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
		if not self.scene.allow_movement_direction(actor.pos, new_pos):
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
	def prevent_automove(self):
		if self.vision.visible_monsters:
			self.fire_event(DiscoverEvent('monsters'))
			return True
		return False
