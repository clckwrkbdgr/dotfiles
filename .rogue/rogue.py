import sys
import functools
import random
import math
import string
import logging
from collections import namedtuple
import curses
import clckwrkbdgr.logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Rect, Size, Matrix, sign
from clckwrkbdgr.math.grid import NestedGrid
from clckwrkbdgr import xdg, utils
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.tui
from src import engine
from src.engine import builders
from src.engine import events
import src.engine.actors, src.engine.items, src.engine.appliances, src.engine.terrain
from src.engine.items import Item

SAVEFILE_VERSION = 7

MOVEMENT = {
		'h' : Point(-1, 0),
		'j' : Point(0, 1),
		'k' : Point(0, -1),
		'l' : Point(1, 0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),
		}

Sprite = namedtuple('Sprite', 'sprite color')

class Terrain(src.engine.terrain.Terrain):
	passable = True
	def save(self, stream):
		stream.write(type(self).__name__)
	@classmethod
	def load(cls, stream):
		cell_type = stream.read()
		return globals()[cell_type]()

class Bog(Terrain):
	_sprite = Sprite('~', 'green')
class Bush(Terrain):
	_sprite = Sprite('"', 'bold_green')
class DeadTree(Terrain):
	_sprite = Sprite('&', 'yellow')
class FrozenGround(Terrain):
	_sprite = Sprite('.', 'white')
class Grass(Terrain):
	_sprite = Sprite('.', 'green')
class Ice(Terrain):
	_sprite = Sprite('.', 'cyan')
class Plant(Terrain):
	_sprite = Sprite('"', 'green')
class Rock(Terrain):
	_sprite = Sprite('^', 'yellow')
	passable = False
class Sand(Terrain):
	_sprite = Sprite('.', 'bold_yellow')
class Snow(Terrain):
	_sprite = Sprite('.', 'bold_white')
class Swamp(Terrain):
	_sprite = Sprite('~', 'cyan')
class Tree(Terrain):
	_sprite = Sprite('&', 'bold_green')
class SwampTree(Terrain):
	_sprite = Sprite('&', 'green')
class Floor(Terrain):
	_sprite = Sprite('.', 'white')
class Wall(Terrain):
	_sprite = Sprite('#', 'white')
	passable = False

class Monster(src.engine.actors.Monster):
	max_hp = None
	def __init__(self, pos):
		super(Monster, self).__init__(pos)
		self.hp = self.max_hp
		self.inventory = []
	def save(self, stream):
		stream.write(','.join(map(str, self.pos)))
		stream.write(self.hp)

		stream.write(len(self.inventory))
		for item in self.inventory:
			stream.write(type(item).__name__)
			item.save(stream)
	def load(self, stream):
		pos = stream.read()
		self.pos.x, self.pos.y = map(int, pos.split(','))
		self.hp = stream.read(int)

		items = stream.read(int)
		for _ in range(items):
			item_type = globals()[stream.read()]
			item = item_type()
			item.load(stream)
			self.inventory.append(item)

class ColoredMonster(Monster):
	def __init__(self, pos, sprite=None, max_hp=None):
		self._sprite = sprite
		self.max_hp = max_hp
		super(ColoredMonster, self).__init__(pos)
	def save(self, stream):
		super(ColoredMonster, self).save(stream)
		stream.write(self._sprite.sprite)
		stream.write(self._sprite.color)
	def load(self, stream):
		super(ColoredMonster, self).load(stream)
		self._sprite = Sprite(stream.read(), stream.read())

class AggressiveColoredMonster(ColoredMonster):
	pass

class Player(Monster):
	_sprite = Sprite('@', 'bold_white')
	init_max_hp = 10
	def __init__(self, pos):
		self.max_hp = self.init_max_hp
		super(Player, self).__init__(pos)
		self.regeneration = 0
	def save(self, stream):
		super(Player, self).save(stream)
		stream.write(self.regeneration)
		stream.write(self.max_hp)
	def load(self, stream):
		super(Player, self).load(stream)
		self.regeneration = stream.read(int)
		self.max_hp = stream.read(int)

class Dweller(Monster):
	max_hp = 10
	def __init__(self, pos, color=None):
		self._sprite = Sprite('@', color)
		super(Dweller, self).__init__(pos)
		self.quest = None
		self.prepared_quest = None
	def save(self, stream):
		super(Dweller, self).save(stream)
		stream.write(self._sprite.color)

		if self.quest:
			stream.write(self.quest[0])
			stream.write(self.quest[1])
			stream.write(self.quest[2])
		else:
			stream.write('')
		if self.prepared_quest:
			stream.write(self.prepared_quest[0])
			stream.write(self.prepared_quest[1])
			stream.write(self.prepared_quest[2])
		else:
			stream.write('')
	def load(self, stream):
		super(Dweller, self).load(stream)
		self._sprite = Sprite(self._sprite.sprite, stream.read())

		self.quest = stream.read()
		if self.quest:
			self.quest = (int(self.quest), stream.read(), stream.read(int))
		else:
			self.quest = None
		self.prepared_quest = stream.read()
		if self.prepared_quest:
			self.prepared_quest = (int(self.prepared_quest), stream.read(), stream.read(int))
		else:
			self.prepared_quest = None

class ColoredSkin(Item):
	def __init__(self, sprite=None, name=None):
		self._sprite = sprite
		self._name = name
	def save(self, stream):
		stream.write(self._sprite.sprite)
		stream.write(self._sprite.color)
		stream.write(self._name)
	def load(self, stream):
		self._sprite = Sprite(stream.read(), stream.read())
		self._name = stream.read()

class ZoneData:
	def save(self, stream):
		pass
	@classmethod
	def load(cls, stream):
		return cls()

class FieldData:
	def __init__(self):
		self.items = []
		self.monsters = []
	def save(self, stream):
		stream.write(len(self.items))
		for item in self.items:
			stream.write(type(item.item).__name__)
			item.item.save(stream)
			stream.write(item.pos)

		stream.write(len(self.monsters))
		for monster in self.monsters:
			stream.write(type(monster).__name__)
			monster.save(stream)
	@classmethod
	def load(cls, stream):
		self = cls()
		items = stream.read(int)
		for _ in range(items):
			item_type = globals()[stream.read()]
			item = item_type()
			item.load(stream)
			pos = stream.read_point()
			self.items.append(src.engine.items.ItemAtPos(pos, item))

		monsters = stream.read(int)
		for _ in range(monsters):
			monster_type = globals()[stream.read()]
			monster = monster_type(Point(0, 0))
			monster.load(stream)
			self.monsters.append(monster)
		return self

class Builder(builders.Builder):
	class Mapping:
		bog = Bog()
		bush = Bush()
		dead_tree = DeadTree()
		frozen_ground = FrozenGround()
		grass = Grass()
		ice = Ice()
		plant = Plant()
		rock = Rock()
		sand = Sand()
		snow = Snow()
		swamp = Swamp()
		tree = Tree()
		swamp_tree = SwampTree()
		floor = Floor()
		wall = Wall()
		def dweller(pos, color):
			return Dweller(pos, color)
		@classmethod
		def monster(cls, pos, sprite, color, strong, aggressive):
			monster_type = AggressiveColoredMonster if aggressive else ColoredMonster
			return monster_type(pos,
				Sprite(sprite.upper() if strong else sprite, color),
				1 + 10 * strong + random.randrange(4),
				)
		@classmethod
		def monster_carrying(cls, pos, sprite, color, strong, aggressive):
			result = cls.monster(pos, sprite, color, strong, aggressive)
			result.inventory.append(ColoredSkin(
				Sprite('*', color),
				'{0} skin'.format(color.replace('_', ' ')),
				))
			return result

	def fill_grid(self, grid):
		self._make_terrain(grid)
		self._building = random.randrange(50) == 0
		if self._building:
			self._building = self._add_building(grid)
	def _add_building(self, grid):
		building = Rect(
				Point(2 + random.randrange(3), 2 + random.randrange(3)),
				Size(6 + random.randrange(3), 6 + random.randrange(3)),
				)
		for x in range(building.width):
			for y in range(building.height):
				grid.set_cell((building.left + x, building.top + y), 'floor')
		for x in range(building.width):
			grid.set_cell((building.left + x, building.top), 'wall')
			grid.set_cell((building.left + x, building.bottom), 'wall')
		for y in range(building.height):
			grid.set_cell((building.left, building.top + y), 'wall')
			grid.set_cell((building.right, building.top + y), 'wall')
		if random.randrange(2) == 0:
			door = building.top + 1 + random.randrange(building.height - 2)
			if random.randrange(2) == 0:
				grid.set_cell((building.left, door), 'floor')
			else:
				grid.set_cell((building.right, door), 'floor')
		else:
			door = building.left + 1 + random.randrange(building.width - 2)
			if random.randrange(2) == 0:
				grid.set_cell((door, building.top), 'floor')
			else:
				grid.set_cell((door, building.bottom), 'floor')
		return building
	def generate_actors(self):
		if self._building:
			yield self._make_dweller(self._building)
			return
		monster_count = random.randrange(5) if random.randrange(5) == 0 else 0
		for _ in range(monster_count):
			yield self._make_monster(self.grid)
	def _make_dweller(self, building):
		dweller_pos = building.topleft + Point(1, 1) + Point(
				random.randrange(building.width - 2),
				random.randrange(building.height - 2),
				)
		colors = [name for name, color in Game.COLORS.items() if color.dweller]
		monster_color = random.choice(colors)
		return dweller_pos, 'dweller', monster_color
	def _make_monster(self, grid):
		monster_pos = Point(
				random.randrange(grid.size.width),
				random.randrange(grid.size.height),
				)
		while self.has_actor(monster_pos):
			monster_pos = Point(
					random.randrange(grid.size.width),
					random.randrange(grid.size.height),
					)
		colors = [name for name, color in Game.COLORS.items() if color.monster]
		normal_colors = [color for color in colors if not color.startswith('bold_')]
		bold_colors = [color for color in colors if color.startswith('bold_')]
		strong = random.randrange(2)
		aggressive = random.randrange(2)
		monster_color = random.choice(bold_colors if aggressive else normal_colors)
		key = 'monster_carrying' if random.randrange(2) else 'monster'
		return (
				monster_pos, key, 
				random.choice(string.ascii_lowercase),
				monster_color, strong, aggressive,
				)

class Forest(Builder):
	def _make_terrain(self, grid):
		grid.clear('grass')
		forest_density = random.randrange(10) * 10
		for _ in range(forest_density):
			grid.set_cell(self.point(), 'tree')
		for _ in range(10):
			grid.set_cell(self.point(), 'bush')
		for _ in range(10):
			grid.set_cell(self.point(), 'plant')

class Desert(Builder):
	def _make_terrain(self, grid):
		grid.clear('sand')
		for _ in range(random.randrange(3)):
			grid.set_cell(self.point(), 'rock')
		for _ in range(10):
			grid.set_cell(self.point(), 'plant')

class Thundra(Builder):
	def _make_terrain(self, grid):
		grid.clear('snow')
		for _ in range(3 + random.randrange(3)):
			grid.set_cell(self.point(), 'ice')
		for _ in range(3 + random.randrange(7)):
			grid.set_cell(self.point(), 'frozen_ground')

class Marsh(Builder):
	def _make_terrain(self, grid):
		grid.clear('swamp')
		for _ in range(100):
			grid.set_cell(self.point(), 'bog')
		for _ in range(random.randrange(100)):
			grid.set_cell(self.point(), 'grass')
		for _ in range(random.randrange(5)):
			grid.set_cell(self.point(), 'swamp_tree')
		for _ in range(random.randrange(10)):
			grid.set_cell(self.point(), 'dead_tree')

def all_monsters(world, raw=False, zone_range=None):
	for zone_index in (zone_range or world.cells):
		zone = world.cells.cell(zone_index)
		if zone is None:
			continue
		for field_index in zone.cells:
			for monster in zone.cells.cell(field_index).data.monsters:
				coord = NestedGrid.Coord(zone_index, field_index, monster.pos)
				if not raw:
					coord = coord.get_global(world)
				yield coord, monster

class NothingToPickUp(events.Event): FIELDS = ''
class NoOneToChat(events.Event): FIELDS = ''
class NoOneToChatInDirection(events.Event): FIELDS = ''
class TooMuchQuests(events.Event): FIELDS = ''
class InventoryIsFull(events.Event): FIELDS = ''
class PickedUpItem(events.Event): FIELDS = 'item'
class ChatThanks(events.Event): FIELDS = ''
class ChatComeLater(events.Event): FIELDS = ''
class ChatQuestReminder(events.Event): FIELDS = 'color item'
class NothingToDrop(events.Event): FIELDS = ''
class DroppedItem(events.Event): FIELDS = 'actor item'
class Bump(events.Event): FIELDS = 'actor target'
class HitMonster(events.Event): FIELDS = 'actor target'
class MonsterDead(events.Event): FIELDS = 'target'
class StareIntoVoid(events.Event): FIELDS = ''

events.Events.on(NothingToPickUp)(lambda _:'Nothing to pick up here.')
events.Events.on(NoOneToChat)(lambda _:'No one to chat with.')
events.Events.on(NoOneToChatInDirection)(lambda _:'No one to chat with in that direction.')
events.Events.on(TooMuchQuests)(lambda _:"Too much quests already.")
events.Events.on(InventoryIsFull)(lambda _:'Inventory is full.')
events.Events.on(PickedUpItem)(lambda _:'Picked up {0}.'.format(_.item.name))

events.Events.on(ChatThanks)(lambda _:'"Thanks. Here you go."')
events.Events.on(ChatComeLater)(lambda _:'"OK, come back later if you want it."')
events.Events.on(ChatQuestReminder)(lambda _:'"Come back with {0} {1}."'.format(_.color, _.item))
events.Events.on(NothingToDrop)(lambda _:'Nothing to drop.')
events.Events.on(DroppedItem)(lambda _:'{0} drop {1}.'.format(_.actor.title(), _.item.name))
events.Events.on(Bump)(lambda _:'{0} bump into {1}.'.format(_.actor.title(), _.target))
events.Events.on(HitMonster)(lambda _:'{0} hit {1}.'.format(_.actor.title(), _.target))
@events.Events.on(MonsterDead)
def monster_is_dead(_):
	if _.target == 'you':
		return 'You died!!!'
	return '{0} is dead.'.format(_.target.title())
events.Events.on(StareIntoVoid)(lambda _:'Will not fall into the void.')

Color = namedtuple('Color', 'fg attr dweller monster')
class Game(engine.Game):
	COLORS = {
			'black': Color(curses.COLOR_BLACK, 0, False, False),
			'red': Color(curses.COLOR_RED, 0, True, True),
			'green': Color(curses.COLOR_GREEN, 0, True, True),
			'blue': Color(curses.COLOR_BLUE, 0, True, True),
			'yellow': Color(curses.COLOR_YELLOW, 0, True, True),
			'cyan': Color(curses.COLOR_CYAN, 0, True, True),
			'magenta': Color(curses.COLOR_MAGENTA, 0, True, True),
			'white': Color(curses.COLOR_WHITE, 0, True, True),
			'bold_black': Color(curses.COLOR_BLACK, curses.A_BOLD, True, True),
			'bold_red': Color(curses.COLOR_RED, curses.A_BOLD, True, True),
			'bold_green': Color(curses.COLOR_GREEN, curses.A_BOLD, True, True),
			'bold_blue': Color(curses.COLOR_BLUE, curses.A_BOLD, True, True),
			'bold_yellow': Color(curses.COLOR_YELLOW, curses.A_BOLD, True, True),
			'bold_cyan': Color(curses.COLOR_CYAN, curses.A_BOLD, True, True),
			'bold_magenta': Color(curses.COLOR_MAGENTA, curses.A_BOLD, True, True),
			'bold_white': Color(curses.COLOR_WHITE, curses.A_BOLD, False, True),
			}
	def __init__(self):
		super(Game, self).__init__()
		self.world = NestedGrid([(256, 256), (16, 16), (16, 16)], [None, ZoneData, FieldData], Terrain)
		self.passed_time = 0
		self.colors = {}
		self._cached_player_pos = None
	def save(self, stream):
		self.world.save(stream)
		stream.write(self.passed_time)
	def load(self, stream):
		self.world.load(stream)
		self.passed_time = stream.read(int)
	def is_finished(self):
		return self.get_player().hp <= 0
	def generate(self):
		zone_pos = Point(
				random.randrange(self.world.cells.size.width),
				random.randrange(self.world.cells.size.height),
				)
		zone = self.generate_zone(zone_pos)

		player_pos = NestedGrid.Coord(
				zone_pos,
				Point(
					random.randrange(zone.cells.size.width),
					random.randrange(zone.cells.size.height),
					),
				Point(
					random.randrange(zone.sizes[-1].width),
					random.randrange(zone.sizes[-1].width),
					),
				)
		player = Player(player_pos.values[-1])
		self.world.get_data(player_pos)[-1].monsters.append(player)
	def autoexpand(self, coord, margin):
		pos = coord.get_global(self.world)
		within_zone = Point(
				pos.x % (self.world.sizes[-2].width * self.world.sizes[-1].width),
				pos.y % (self.world.sizes[-2].height * self.world.sizes[-1].height),
				)
		close_to_zone_boundaries = False
		in_world_pos = coord.values[0]
		expansion = Point(0, 0)
		if within_zone.x - 40 < 0:
			close_to_zone_boundaries = True
			expansion.x = -1
		if within_zone.x + 40 >= self.world.cells.cell(in_world_pos).full_size.width:
			close_to_zone_boundaries = True
			expansion.x = +1
		if within_zone.y - 40 < 0:
			close_to_zone_boundaries = True
			expansion.y = -1
		if within_zone.y + 40 >= self.world.cells.cell(in_world_pos).full_size.height:
			close_to_zone_boundaries = True
			expansion.y = +1
		if not close_to_zone_boundaries:
			return
		if expansion.x:
			new_pos = in_world_pos + Point(expansion.x, 0)
			if self.world.cells.valid(new_pos) and self.world.cells.cell(new_pos) is None:
				self.generate_zone(new_pos)
		if expansion.y:
			new_pos = in_world_pos + Point(0, expansion.y)
			if self.world.cells.valid(new_pos) and self.world.cells.cell(new_pos) is None:
				self.generate_zone(new_pos)
		if expansion.x * expansion.y:
			new_pos = in_world_pos + expansion
			if self.world.cells.valid(new_pos) and self.world.cells.cell(new_pos) is None:
				self.generate_zone(new_pos)
	def generate_zone(self, zone_pos):
		zone = self.world.make_subgrid(zone_pos)
		for pos in zone.cells:
			field = zone.make_subgrid(pos)
			builder_type = random.choice(utils.all_subclasses(Builder))
			builder = builder_type(random, field.cells)
			builder.generate()
			builder.make_grid()
			field.data.monsters.extend(builder.make_actors())
		return zone
	def iter_cells(self, view_rect):
		viewport_topleft = NestedGrid.Coord.from_global(view_rect.topleft, self.world)
		viewport_bottomright = NestedGrid.Coord.from_global(view_rect.bottomright, self.world)
		raw_viewport = Rect(Point(0, 0), view_rect.size)
		raw_viewport_center = Point(*(raw_viewport.size // 2))
		view_shift = view_rect.topleft

		full_zone_size = Size(
				self.world.sizes[-2].width * self.world.sizes[-1].width,
				self.world.sizes[-2].height * self.world.sizes[-1].height,
				)
		for zone_index in iter_rect(viewport_topleft.values[0], viewport_bottomright.values[0]):
			zone = self.world.cells.cell(zone_index)
			if zone is None:
				continue
			zone_shift = Point(
						zone_index.x * full_zone_size.width,
						zone_index.y * full_zone_size.height,
						)
			for field_index in zone.cells:
				field = zone.cells.cell(field_index)
				field_rect = Rect(zone_shift + Point(
							field_index.x * field.full_size.width,
							field_index.y * field.full_size.height,
							), field.full_size)
				control_points = [
						Point(field_rect.left, field_rect.top),
						Point(field_rect.right, field_rect.top),
						Point(field_rect.left, field_rect.bottom),
						Point(field_rect.right, field_rect.bottom),
						]
				if not any(raw_viewport.contains(pos - view_shift, with_border=True) for pos in control_points):
					continue
				for pos in field.cells:
					if not view_rect.contains(pos + field_rect.topleft, with_border=True):
						continue
					coord_pos = NestedGrid.Coord(zone_index, field_index, pos)
					
					yield ((pos + field_rect.topleft), self.get_cell_info(coord_pos, context=field))
	def get_cell_info(self, pos, context=None):
		field = context
		return (
				field.cells.cell(pos.values[-1]),
				[], # No objects.
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)
	def get_player(self):
		player, _ = self._get_player_data()
		return player
	def get_player_coord(self):
		_, coord = self._get_player_data()
		return coord
	def _get_player_data(self):
		if self._cached_player_pos is None:
			player, self._cached_player_pos = next((monster, coord) for coord, monster in all_monsters(self.world, raw=True) if isinstance(monster, Player))
			return player, self._cached_player_pos
		expected_zone_index = self._cached_player_pos.values[0]
		expected_zone = self.world.cells.cell(expected_zone_index)
		expected_field_index = self._cached_player_pos.values[1]
		expected_field = expected_zone.cells.cell(expected_field_index)
		# Expecting at the last remembered field:
		for monster in expected_field.data.monsters:
			if isinstance(monster, Player):
				self._cached_player_pos = NestedGrid.Coord(expected_zone_index, expected_field_index, monster.pos)
				return monster, self._cached_player_pos
		# Not found in the field.
		# Checking the whole last remembered zone:
		for coord, monster in all_monsters(self.world, raw=True, zone_range=[expected_zone_index]):
			if isinstance(monster, Player):
				self._cached_player_pos = coord
				return monster, self._cached_player_pos
		# Not found in the last remembered zone.
		# Checking adjacent zones:
		adjacent_zones = set(iter_rect(
			expected_zone_index - Point(1, 1),
			expected_zone_index + Point(1, 1),
			)) - {expected_zone_index}
		for coord, monster in all_monsters(self.world, raw=True, zone_range=adjacent_zones):
			if isinstance(monster, Player):
				self._cached_player_pos = coord
				return monster, self._cached_player_pos
		# Not found in adjacent zones.
		# Performing full lookup:
		player, self._cached_player_pos = next((monster, coord) for coord, monster in all_monsters(self.world, raw=True) if isinstance(monster, Player))
		return player, self._cached_player_pos

	def iter_items_at(self, pos):
		zone_items = self.world.get_data(pos)[-1].items
		for item_pos, item in zone_items:
			if pos.values[-1] == item_pos:
				yield item
	def iter_actors_at(self, pos, with_player=False):
		zone_actors = self.world.get_data(pos)[-1].monsters
		for actor in zone_actors:
			if not with_player and isinstance(actor, Player):
				continue
			if pos.values[-1] == actor.pos:
				yield actor

def iter_rect(topleft, bottomright):
	for x in range(topleft.x, bottomright.x + 1):
		for y in range(topleft.y, bottomright.y + 1):
			yield Point(x, y)

InventoryKeys = clckwrkbdgr.tui.Keymapping()
InventoryKeys.map(list('abcdefghijlkmnopqrstuvwxyz'), lambda key:str(key))
InventoryKeys.map(clckwrkbdgr.tui.Key.ESCAPE, 'cancel')
class InventoryMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = False
	KEYMAPPING = InventoryKeys
	def __init__(self, inventory, caption=None, on_select=None):
		self.inventory = inventory
		self.caption = caption
		self.on_select = on_select
	def redraw(self, ui):
		if True:
			if self.caption:
				ui.print_line(0, 0, self.caption)
			accumulated = []
			for shortcut, item in zip(string.ascii_lowercase, self.inventory):
				for other in accumulated:
					if other[1].name == item.name:
						other[2] += 1
						break
				else:
					accumulated.append([shortcut, item, 1])
			for index, (shortcut, item, amount) in enumerate(accumulated):
				column = index // 20
				index = index % 20
				ui.print_line(index + 1, column * 40 + 0, '[{0}] '.format(shortcut))
				ui.print_line(index + 1, column * 40 + 4, item.sprite.sprite, item.sprite.color)
				if amount > 1:
					ui.print_line(index + 1, column * 40 + 6, '- {0} (x{1})'.format(item.name, amount))
				else:
					ui.print_line(index + 1, column * 40 + 6, '- {0}'.format(item.name))
	def action(self, control):
		if control == 'cancel':
			return None
		if self.on_select:
			selected = ord(control) - ord('a')
			if selected < 0 or len(self.inventory) <= selected:
				self.caption = 'No such item: {0}'.format(control)
			else:
				self.on_select(selected)
				return None
		return True

DialogKeys = clckwrkbdgr.tui.Keymapping()
DialogKeys.map(list('yY'), True)

QuestLogKeys = clckwrkbdgr.tui.Keymapping()
QuestLogKeys.map(clckwrkbdgr.tui.Key.ESCAPE, 'cancel')

def main(ui):
	for name, color in Game.COLORS.items():
		ui.init_color(name, color.fg, color.attr)

	game = Game()
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'rogue.sav')
	with savefile.get_reader() as reader:
		if reader:
			assert reader.version == SAVEFILE_VERSION, (reader.version, SAVEFILE_VERSION, savefile.filename)
			game.load(reader)
		else:
			game.generate()

	main_game = MainGameMode(game)
	loop = clckwrkbdgr.tui.ModeLoop(ui)
	loop.run(main_game)
	if not game.is_finished():
		with savefile.save(SAVEFILE_VERSION) as writer:
			game.save(writer)
	else:
		savefile.unlink()

Keys = clckwrkbdgr.tui.Keymapping()
class MainGameMode(clckwrkbdgr.tui.Mode):
	KEYMAPPING = Keys
	def __init__(self, game):
		self.game = game
		self.viewport = Rect((0, 0), (61, 23))
		self.center = Point(*(self.viewport.size // 2))
		self.centered_viewport = Rect((-self.center.x, -self.center.y), self.viewport.size)
		self.messages = []
	def redraw(self, ui):
		game = self.game
		view_rect = Rect(
				game.get_player_coord().get_global(game.world) + self.centered_viewport.topleft,
				self.centered_viewport.size,
				)
		for _pos, (_terrain, _objects, _items, _monsters) in game.iter_cells(view_rect):
			if _monsters:
				entity = _monsters[-1]
			elif _items:
				entity = _items[-1]
			elif _objects:
				entity = _objects[-1]
			else:
				entity = _terrain
			sprite = entity.sprite
			screen_pos = _pos - view_rect.topleft
			ui.print_char(screen_pos.x, screen_pos.y, sprite.sprite, sprite.color)

		hud_pos = self.viewport.right + 1
		for row in range(5):
			ui.print_line(row, hud_pos, " " * (80 - hud_pos))
		ui.print_line(0, hud_pos, "@{0:02X}.{1:X}.{2:X};{3:02X}.{4:X}.{5:X}".format(
			game.get_player_coord().values[0].x,
			game.get_player_coord().values[1].x,
			game.get_player_coord().values[2].x,
			game.get_player_coord().values[0].y,
			game.get_player_coord().values[1].y,
			game.get_player_coord().values[2].y,
			))
		ui.print_line(1, hud_pos, "T:{0}".format(game.passed_time))
		ui.print_line(2, hud_pos, "hp:{0}/{1}".format(game.get_player().hp, game.get_player().max_hp))
		ui.print_line(3, hud_pos, "inv:{0}".format(len(game.get_player().inventory)))
		item_here = next(game.iter_items_at(game.get_player_coord()), None)
		if item_here:
			ui.print_line(4, hud_pos, "here:{0}".format(item_here.sprite.sprite))

		ui.print_line(24, 0, " " * 80)
		self.messages.extend(game.process_events())
		if self.messages:
			to_remove, message_line = clckwrkbdgr.text.wrap_lines(self.messages, width=80)
			if not to_remove:
				del self.messages[:]
			elif to_remove > 0:
				self.messages = self.messages[to_remove:]
			else:
				self.messages[0] = self.messages[0][-to_remove:]
			ui.print_line(24, 0, message_line)
	def pre_action(self):
		self.step_taken = False
		return True
	def get_keymapping(self):
		if self.messages or self.game.get_player().hp <= 0:
			return None
		return super().get_keymapping()
	@Keys.bind('S')
	def exit_game(self):
		return 'quit'
	@Keys.bind('.')
	def wait(self):
		if True:
			self.step_taken = True
	@Keys.bind('g')
	def grab_item(self):
		game = self.game
		if True:
			item = next(game.iter_items_at(game.get_player_coord()), None)
			if not item:
				self.game.fire_event(NothingToPickUp())
			elif len(game.get_player().inventory) >= 26:
				self.game.fire_event(InventoryIsFull())
			else:
				game.get_player().inventory.append(item)
				game.world.get_data(game.get_player_coord())[-1].items.remove(item)
				self.game.fire_event(PickedUpItem(item))
				self.step_taken = True
	@Keys.bind('C')
	def char(self):
		game = self.game
		player_pos = game.get_player_coord().get_global(game.world)
		if True:
			npcs = [
					monster for monster_pos, monster
					in all_monsters(game.world)
					if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1
					and isinstance(monster, Dweller)
					]
			questing = [
					npc for _, npc in all_monsters(game.world)
					if isinstance(npc, Dweller)
					and npc.quest
					]
			if not npcs:
				self.game.fire_event(NoOneToChat())
			elif len(questing) > 20:
				self.game.fire_event(TooMuchQuests())
			else:
				if len(npcs) > 1:
					def _on_direction(direction):
						dest = player_pos + dialog.answer
						npcs = [npc for npc in npcs if npc.pos == dest]
						return self._chat_with_npcs(npcs)
					return DirectionDialogMode(on_direction=_on_direction)
				return self._chat_with_npcs(npcs)
	def _chat_with_npcs(self, npcs):
		if True:
			if True:
				if npcs:
					npc = npcs[0]
					return self._chat_with_npc(npc)
				else:
					self.game.fire_event(NoOneToChatInDirection())
	def _chat_with_npc(self, npc):
		game = self.game
		if True:
			if True:
				if True:
					if npc.quest:
						required_amount, required_name, bounty = npc.quest
						have_required_items = [
								item for item in game.get_player().inventory
								if item.name == required_name
								][:required_amount]
						if len(have_required_items) >= required_amount:
							def _on_yes():
								self.game.fire_event(ChatThanks())
								for item in have_required_items:
									game.get_player().inventory.remove(item)
								if game.get_player().hp == game.get_player().max_hp:
									game.get_player().hp += bounty
								game.get_player().max_hp += bounty
								npc.quest = None
							def _on_no():
								self.game.fire_event(ChatComeLater())
							return TradeDialogMode('"You have {0} {1}. Trade it for +{2} max hp?" (y/n)'.format(*(self.npc.quest)),
										on_yes=_on_yes, on_no=_on_no)
						else:
							self.game.fire_event(ChatQuestReminder(*(npc.quest)))
					else:
						if not npc.prepared_quest:
							amount = 1 + random.randrange(3)
							bounty = max(1, amount // 2 + 1)
							colors = [name for name, color in game.COLORS.items() if color.monster]
							color = random.choice(colors).replace('_', ' ') + ' skin'
							npc.prepared_quest = (amount, color, bounty)
						def _on_yes():
							npc.quest = npc.prepared_quest
							npc.prepared_quest = None
						def _on_no():
							self.game.fire_event(ChatComeLater())
						return TradeDialogMode('"Bring me {0} {1}, trade it for +{2} max hp, deal?" (y/n)'.format(*(npc.prepared_quest)),
										 on_yes=_on_yes, on_no=_on_no)
	@Keys.bind('q')
	def show_questlog(self):
		game = self.game
		if True:
			questing = [
					(coord, npc) for coord, npc in all_monsters(game.world, raw=True)
					if isinstance(npc, Dweller)
					and npc.quest
					]
			quest_log = QuestLog(questing)
			return quest_log
	@Keys.bind('i')
	def display_inventory(self):
		return InventoryMode(self.game.get_player().inventory)
	@Keys.bind('d')
	def drop_item(self):
		game = self.game
		if True:
			if not game.get_player().inventory:
				self.game.fire_event(NothingToDrop())
			else:
				def _on_select_item(menu_choice):
					item = game.get_player().inventory.pop(menu_choice)
					item_pos = game.get_player_coord().values[-1]
					game.world.get_data(game.get_player_coord())[-1].items.append(src.engine.items.ItemAtPos(item_pos, item))
					self.game.fire_event(DroppedItem('you', item))
					self.step_taken = True
				return InventoryMode(
						game.get_player().inventory,
						caption="Select item to drop (a-z/ESC):",
						on_select=_on_select_item
					)
	@Keys.bind(list('hjklyubn'), lambda key:MOVEMENT[str(key)])
	def move_player(self, control):
		game = self.game
		player_pos = game.get_player_coord().get_global(game.world)
		if True:
			new_pos = player_pos + control
			dest_pos = NestedGrid.Coord.from_global(new_pos, game.world)
			dest_field_data = None
			dest_cell = None
			if game.world.valid(dest_pos):
				dest_field_data = game.world.get_data(dest_pos)[-1]
				dest_cell = game.world.cell(dest_pos)
			monster = next(game.iter_actors_at(dest_pos), None)
			if monster:
				if isinstance(monster, Dweller):
					self.game.fire_event(Bump('you', 'dweller'))
				else:
					monster.hp -= 1
					self.game.fire_event(HitMonster('you', 'monster'))
					if monster.hp <= 0:
						dest_field_data.monsters.remove(monster)
						self.game.fire_event(MonsterDead('monster'))
						for item in monster.inventory:
							item_pos = monster.pos
							monster.inventory.remove(item)
							dest_field_data.items.append(src.engine.items.ItemAtPos(item_pos, item))
							self.game.fire_event(DroppedItem('monster', item))
			elif dest_cell is None:
				self.game.fire_event(StareIntoVoid())
			elif dest_cell.passable:
				player = game.get_player()
				current_field_data = game.world.get_data(self.game.get_player_coord())[-1]
				if current_field_data != dest_field_data:
					current_field_data.monsters.remove(player)
					dest_field_data.monsters.append(player)
				player.pos = dest_pos.values[-1]
				game.autoexpand(self.game.get_player_coord(), Size(40, 40))
			self.step_taken = True
	def action(self, control):
		if isinstance(control, clckwrkbdgr.tui.Key):
			if self.messages:
				return True
			if self.game.get_player().hp <= 0:
				return False
		if control == 'quit':
			return False
		game = self.game
		if self.step_taken:
			player_pos = game.get_player_coord().get_global(game.world)
			if game.get_player().hp < game.get_player().max_hp:
				game.get_player().regeneration += 1
				while game.get_player().regeneration >= 10:
					game.get_player().regeneration -= 10
					game.get_player().hp += 1
					if game.get_player().hp >= game.get_player().max_hp:
						game.get_player().hp = game.get_player().max_hp

			game.passed_time += 1

			monster_action_length = 10
			monster_action_range = Point(monster_action_length, monster_action_length)
			monster_zone_topleft = NestedGrid.Coord.from_global(player_pos - monster_action_range, game.world)
			monster_zone_bottomright = NestedGrid.Coord.from_global(player_pos + monster_action_range, game.world)
			monster_zone_range = iter_rect(monster_zone_topleft.values[0], monster_zone_bottomright.values[0])
			already_acted_monsters_from_previous_fields = []
			for monster_coord, monster in all_monsters(game.world, raw=True, zone_range=monster_zone_range):
				if monster in already_acted_monsters_from_previous_fields:
					continue
				if isinstance(monster, Dweller):
					continue
				if isinstance(monster, Player):
					continue
				monster_pos = monster_coord.get_global(game.world)
				if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1:
					game.get_player().hp -= 1
					self.game.fire_event(HitMonster('monster', 'you'))
					if game.get_player().hp <= 0:
						self.game.fire_event(MonsterDead('you'))
				elif isinstance(monster, AggressiveColoredMonster) and math.hypot(monster_pos.x - player_pos.x, monster_pos.y - player_pos.y) <= monster_action_length:
					shift = Point(
							sign(player_pos.x - monster_pos.x),
							sign(player_pos.y - monster_pos.y),
							)
					new_pos = monster_pos + shift
					dest_pos = NestedGrid.Coord.from_global(new_pos, game.world)
					dest_field_data = game.world.get_data(dest_pos)[-1]
					dest_cell = game.world.cell(dest_pos)
					if any(True for _ in game.iter_actors_at(dest_pos)):
						self.game.fire_event(Bump('monster', 'monster.'))
					elif dest_cell.passable:
						current_field_data = game.world.get_data(monster_coord)[-1]
						if current_field_data != dest_field_data:
							current_field_data.monsters.remove(monster)
							dest_field_data.monsters.append(monster)
							already_acted_monsters_from_previous_fields.append(monster)
						monster.pos = dest_pos.values[-1]
		return True

DirectionKeys = clckwrkbdgr.tui.Keymapping()
class DirectionDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DirectionKeys
	def __init__(self, on_direction=None):
		self.on_direction = on_direction
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, "Too crowded. Chat in which direction?")
	@DirectionKeys.bind(list('hjklyubn'), lambda key:MOVEMENT[str(key)])
	def choose_direction(self, direction):
		if self.on_direction:
			return self.on_direction(direction)
		return False
	def action(self, control):
		return False

class TradeDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DialogKeys
	def __init__(self, question, on_yes=None, on_no=None):
		self.question = question
		self.on_yes = on_yes
		self.on_no = on_no
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, self.question)
	def action(self, control):
		if control:
			if self.on_yes:
				self.on_yes()
		else:
			if self.on_no:
				self.on_no()

class QuestLog(clckwrkbdgr.tui.Mode):
	TRANSPARENT = False
	KEYMAPPING = QuestLogKeys
	def __init__(self, quests):
		self.quests = quests
	def redraw(self, ui):
		if not self.quests:
			ui.print_line(0, 0, "No current quests.")
		else:
			ui.print_line(0, 0, "Current quests:")
		for index, (coord, npc) in enumerate(self.quests):
			ui.print_line(index + 1, 0, "@ {2}: Bring {0} {1}.".format(
				npc.quest[0],
				npc.quest[1],
				coord,
				))
	def action(self, control):
		return control != 'cancel'

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	if debug:
		clckwrkbdgr.logging.init(
			'rogue', debug=True, filename='rogue.log', stream=None,
			)
	with clckwrkbdgr.tui.Curses() as ui:
		main(ui)

if __name__ == '__main__':
	cli()
