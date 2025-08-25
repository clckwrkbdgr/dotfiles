from . import pcg
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr.math import Point, Direction, Matrix, Size, Rect
import logging
Log = logging.getLogger('rogue')
from .engine import items, actors, scene, appliances
from . import engine
from .engine import auto
from .engine import math, vision
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

class DescendEvent(ImportantEvent):
	""" Descended to another level. """
	FIELDS = 'actor'
class GrabItemEvent(ImportantEvent):
	""" Grabs something from the floor. """
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

class Vision(vision.Vision):
	def __init__(self, scene):
		super(Vision, self).__init__(scene)
		self.visited = Matrix(scene.strata.size, False)
		self.field_of_view = clckwrkbdgr.math.algorithm.FieldOfView(10)
		self.visible_monsters = []
		self.visible_items = []
	def load(self, reader):
		self.visited = reader.read_matrix(lambda c:c=='1')
	def save(self, writer):
		writer.write(self.visited)
	def is_visible(self, pos):
		return self.field_of_view.is_visible(pos.x, pos.y)
	def is_explored(self, pos):
		return self.visited.cell(pos)
	def visit(self, monster):
		""" Recalculates visibility/FOV for the player.
		May produce Discover events, if some objects come into vision.
		Remembers already seen objects.
		"""
		scene = self.scene
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
	def one_time(self):
		return True
	def make_vision(self):
		return Vision(self)
	def generate(self, id):
		builder = self.rng.choice(self.builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		Log.debug('With RNG: {0}...'.format(self.rng.value))
		builder = builder(self.rng, Size(80, 23))
		settler = builder
		Log.debug("Populating dungeon: {0}".format(settler))
		builder.generate()

		self.strata = builder.make_grid()

		_appliances = list(builder.make_appliances())
		self._start_pos = next(_pos for _pos, _name in _appliances if _name == 'start')
		self.appliances = [_entry for _entry in _appliances if _entry.obj != 'start']

		exit_stairs = next(_entry.obj for _entry in self.appliances if isinstance(_entry.obj, appliances.LevelPassage))
		if '/' in id:
			level_id, index = id.split('/')
		else:
			level_id, index = id, 0
		index = str(int(index) + 1)
		exit_stairs.level_id = '/'.join((level_id, index))

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
	def valid(self, pos):
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
	def can_move(self, actor, pos):
		if not self.allow_movement_direction(actor.pos, pos):
			return False
		return self.strata.cell(pos).passable
	def drop_item(self, item_at_pos):
		self.items.append(item_at_pos)
	def rip(self, actor):
		for item in actor.drop_all():
			self.items.append(item)
			yield item.item
		self.monsters.remove(actor)
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
	"""
	def end_turn(self):
		if self.scene.get_player():
			self.scene.get_player().spend_action_points()
	def toggle_god_vision(self):
		self.god.vision = not self.god.vision
	def toggle_god_noclip(self):
		self.god.noclip = not self.god.noclip
	def get_viewport(self):
		""" Returns current viewport rect. """
		return Rect(Point(0, 0), self.scene.strata.size)
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
		self.update_vision()
	def descend(self):
		""" Descends onto new level, when standing on exit pos.
		Generates new level.
		Otherwise does nothing.
		"""
		for obj in self.scene.iter_appliances_at(self.scene.get_player().pos):
			if isinstance(obj, appliances.LevelPassage):
				self.fire_event(DescendEvent(self.scene.get_player()))
				self.travel(self.scene.get_player(), obj.level_id, obj.connected_passage)
				break
	def prevent_automove(self):
		if self.vision.visible_monsters:
			self.fire_event(engine.Events.Discover('monsters'))
			return True
		return False
