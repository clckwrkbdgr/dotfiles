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
from clckwrkbdgr.math import Point, Rect, Size, Matrix, sign, distance
from clckwrkbdgr.math.grid import NestedGrid
from clckwrkbdgr import xdg, utils
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.tui
from src import engine
from src.engine import builders, scene
from src.engine import events, auto, vision
import src.engine.actors, src.engine.items, src.engine.appliances, src.engine.terrain
from src.engine.items import Item
from src.engine.terrain import Terrain
from src.engine.actors import Monster
from src.engine import ui
from src.engine import ui as UI
from src.engine.ui import Sprite
from src.engine import Events

SAVEFILE_VERSION = 13

class Void(Terrain):
	_sprite = Sprite(' ', 'black')
	_passable = False

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
	_passable = False
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
	_passable = False

class RealMonster(Monster):
	pass

class Player(Monster, src.engine.actors.Player):
	_sprite = Sprite('@', 'bold_white')
	_name = 'you'
	_vision = 10
	_attack = 1
	_hostile_to = [RealMonster]
	init_max_hp = 10
	_max_inventory = 26
	def __init__(self, pos):
		self._max_hp = self.init_max_hp
		super(Player, self).__init__(pos)
		self.regeneration = 0
	def save(self, stream):
		super(Player, self).save(stream)
		stream.write(self.regeneration)
		stream.write(self.max_hp)
	def load(self, stream):
		super(Player, self).load(stream)
		self.regeneration = stream.read(int)
		self._max_hp = stream.read(int)
	def apply_auto_effects(self):
		if self.hp >= self.max_hp:
			return
		self.regeneration += 1
		while self.regeneration >= 10:
			self.regeneration -= 10
			self.affect_health(+1)
			if self.hp >= self.max_hp:
				self.hp = self.max_hp

class ColoredMonster(RealMonster, src.engine.actors.Defensive):
	_attack = 1
	_max_inventory = 1
	_hostile_to = [Player]
	_name = 'monster'
	def __init__(self, pos, sprite=None, max_hp=None):
		self._sprite = sprite
		self._max_hp = max_hp
		super(ColoredMonster, self).__init__(pos)
	def save(self, stream):
		super(ColoredMonster, self).save(stream)
		stream.write(self._sprite.sprite)
		stream.write(self._sprite.color)
		stream.write(self._max_hp)
	def load(self, stream):
		super(ColoredMonster, self).load(stream)
		self._sprite = Sprite(stream.read(), stream.read())
		self._max_hp = stream.read_int()

MAX_MONSTER_ACTION_LENGTH = 10

class AggressiveColoredMonster(ColoredMonster):
	_vision = 10
	def act(self, game):
		self_pos = self.coord.get_global(game.scene.world)
		monster_action_range = Rect(
				self_pos - Point(self.vision, self.vision),
				Size(1 + self.vision * 2, 1 + self.vision * 2),
				)
		closest = []
		for monster in game.scene.iter_actors_in_rect(monster_action_range):
			if not self.is_hostile_to(monster):
				continue
			monster_pos = monster.coord.get_global(game.scene.world)
			closest.append((
				distance(self_pos, monster_pos),
				monster.coord, monster,
				))
		if not closest:
			return
		_, monster_coord, monster = sorted(closest)[0]
		monster_pos = monster_coord.get_global(game.scene.world)
		if max(abs(self_pos.x - monster_pos.x), abs(self_pos.y - monster_pos.y)) <= 1:
			game.attack(self, monster)
			return
		vision = game.scene.make_vision(self)
		vision.visit(self)
		if vision.is_visible(monster_pos):
			shift = Point(
					sign(monster_pos.x - self_pos.x),
					sign(monster_pos.y - self_pos.y),
					)
			game.move_actor(self, shift)

class Dweller(Monster, src.engine.actors.Neutral):
	_max_hp = 10
	_name = 'dweller'
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
		super(ColoredSkin, self).save(stream)
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
			item.save(stream)

		stream.write(len(self.monsters))
		for monster in self.monsters:
			monster.save(stream)
	@classmethod
	def load(cls, stream):
		self = cls()
		items = stream.read(int)
		for _ in range(items):
			self.items.append(stream.read(src.engine.items.ItemAtPos))

		monsters = stream.read(int)
		for _ in range(monsters):
			self.monsters.append(src.engine.actors.Actor.load(stream))
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
			result.grab(ColoredSkin(
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

class NoOneToChat(events.Event): FIELDS = ''
class NoOneToChatInDirection(events.Event): FIELDS = ''
class TooMuchQuests(events.Event): FIELDS = ''
class ChatThanks(events.Event): FIELDS = ''
class ChatComeLater(events.Event): FIELDS = ''
class ChatQuestReminder(events.Event): FIELDS = 'color item'

events.Events.on(Events.NothingToPickUp)(lambda _:'Nothing to pick up here.')
events.Events.on(NoOneToChat)(lambda _:'No one to chat with.')
events.Events.on(NoOneToChatInDirection)(lambda _:'No one to chat with in that direction.')
events.Events.on(TooMuchQuests)(lambda _:"Too much quests already.")
events.Events.on(Events.InventoryIsFull)(lambda _:'Inventory is full.')
events.Events.on(Events.GrabItem)(lambda _:'Picked up {0}.'.format(_.item.name))
events.Events.on(Events.Welcome)(lambda _:'Welcome!')
events.Events.on(Events.WelcomeBack)(lambda _:'Welcome back!')

events.Events.on(ChatThanks)(lambda _:'"Thanks. Here you go."')
events.Events.on(ChatComeLater)(lambda _:'"OK, come back later if you want it."')
events.Events.on(ChatQuestReminder)(lambda _:'"Come back with {0} {1}."'.format(_.color, _.item))
events.Events.on(Events.InventoryIsEmpty)(lambda _:'Inventory is empty.')
events.Events.on(Events.NotConsumable)(lambda _:'Cannot eat {0}.'.format(_.item.name))
events.Events.on(Events.DropItem)(lambda _:'{0} drop {1}.'.format(_.actor.name.title(), _.item.name))
events.Events.on(Events.BumpIntoTerrain)(lambda _:None)
events.Events.on(Events.Move)(lambda _:None)
events.Events.on(Events.Health)(lambda _:None)
events.Events.on(Events.BumpIntoActor)(lambda _:'{0} bump into {1}.'.format(_.actor.name.title(), _.target.name))
events.Events.on(Events.Attack)(lambda _:'{0} hit {1}.'.format(_.actor.name.title(), _.target.name))
@events.Events.on(Events.Discover)
def on_discover(event):
	if hasattr(event.obj, 'name'):
		if isinstance(event.obj, ColoredMonster):
			return '{1} {0}!'.format(event.obj.name, event.obj.sprite.color)
		return '{0}!'.format(event.obj.name)
	else: # pragma: no cover
		return '{0}!'.format(event.obj)
@events.Events.on(Events.AutoStop)
def stop_auto_activities(event):
	if isinstance(event.reason[0], src.engine.actors.Actor):
		return 'There are monsters nearby!'
	return 'There are {0} nearby!'.format(', '.join(map(str, event.reason)))
@events.Events.on(Events.Death)
def monster_is_dead(_):
	if _.target.name == 'you':
		return 'You died!!!'
	return '{0} is dead.'.format(_.target.name.title())
events.Events.on(Events.StareIntoVoid)(lambda _:'Will not fall into the void.')

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
	def make_scene(self, scene_id):
		return Scene()
	def make_player(self):
		return Player(None)

class Vision(vision.OmniVision):
	def __init__(self, scene):
		super(Vision, self).__init__(scene)
		self.visible_monsters = []
		self._first_visit = True
	def iter_important(self):
		for _ in self.visible_monsters:
			yield _
	def visit(self, actor):
		actor_pos = self.scene.get_global_pos(actor)
		vision_range = Rect( # Twice as wide.
				actor_pos - Point(actor.vision * 3 - 1, actor.vision),
				Size(1 + actor.vision * 3 * 2 - 1, 1 + actor.vision * 2),
				)
		current_visible_monsters = []
		for monster in self.scene.iter_actors_in_rect(vision_range):
			if monster == actor:
				continue
			if monster not in self.visible_monsters:
				if not self._first_visit:
					yield monster
			current_visible_monsters.append(monster)
		if self._first_visit:
			self._first_visit = False
		self.visible_monsters = current_visible_monsters

class MonsterVision(vision.Vision):
	def __init__(self, scene):
		super(MonsterVision, self).__init__(scene)
		self.monster = None
	def is_visible(self, pos):
		return clckwrkbdgr.math.distance(self.scene.get_global_pos(self.monster), pos) <= self.monster.vision
	def visit(self, monster):
		self.monster = monster

class Scene(scene.Scene):
	def __init__(self):
		self.world = NestedGrid([(256, 256), (16, 16), (16, 16)], [None, ZoneData, FieldData], Terrain)
		self._cached_player_pos = None
	@classmethod
	def get_autoexplorer_class(cls): # pragma: no cover -- TODO
		return auto.EndlessAreaExplorer
	def make_vision(self, actor):
		if isinstance(actor, src.engine.actors.Player):
			return Vision(self)
		return MonsterVision(self)
	def generate(self, id):
		zone_pos = Point(
				random.randrange(self.world.cells.size.width),
				random.randrange(self.world.cells.size.height),
				)
		zone = self.generate_zone(zone_pos)

		self._player_pos = NestedGrid.Coord(
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
	def exit_actor(self, actor):
		dest_pos = self.get_global_pos(actor)
		dest_pos = NestedGrid.Coord.from_global(dest_pos, self.world)
		dest_field_data = self.world.get_data(dest_pos)[-1]
		dest_field_data.monsters.remove(actor)
	def enter_actor(self, actor, location):
		actor.pos = self._player_pos.values[-1]
		self.world.get_data(self._player_pos)[-1].monsters.append(actor)
	def rip(self, actor):
		dest_pos = self.get_global_pos(actor)
		dest_pos = NestedGrid.Coord.from_global(dest_pos, self.world)
		dest_field_data = self.world.get_data(dest_pos)[-1]
		for item in actor.drop_all():
			dest_field_data.items.append(item)
			yield item.item
		dest_field_data.monsters.remove(actor)
	def drop_item(self, item_at_pos):
		coord = NestedGrid.Coord.from_global(item_at_pos.pos, self.world)
		item_at_pos.pos = coord.values[-1]
		self.world.get_data(coord)[-1].items.append(item_at_pos)
	def take_item(self, item_at_pos):
		coord = NestedGrid.Coord.from_global(item_at_pos.pos, self.world)
		items = self.world.get_data(coord)[-1].items
		item_at_pos.pos = coord.values[-1]
		found = next(_ for _ in items if _ == item_at_pos)
		items.remove(found)
		return found.item
	def save(self, stream):
		self.world.save(stream)
	def load(self, stream):
		super(Scene, self).load(stream)
		self.world.load(stream)
	def recalibrate(self, pos, margin):
		within_zone = Point(
				pos.x % (self.world.sizes[-2].width * self.world.sizes[-1].width),
				pos.y % (self.world.sizes[-2].height * self.world.sizes[-1].height),
				)
		close_to_zone_boundaries = False
		coord = NestedGrid.Coord.from_global(pos, self.world)
		in_world_pos = coord.values[0]
		expansion = Point(0, 0)
		if within_zone.x - margin.width < 0:
			close_to_zone_boundaries = True
			expansion.x = -1
		if within_zone.x + margin.width >= self.world.cells.cell(in_world_pos).full_size.width:
			close_to_zone_boundaries = True
			expansion.x = +1
		if within_zone.y - margin.height < 0:
			close_to_zone_boundaries = True
			expansion.y = -1
		if within_zone.y + margin.height >= self.world.cells.cell(in_world_pos).full_size.height:
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
	def valid(self, pos):
		pos = NestedGrid.Coord.from_global(pos, self.world)
		return self.world.valid(pos)
	def get_cell_info(self, pos, context=None):
		field = context
		if field is None:
			if isinstance(pos, Point):
				pos = NestedGrid.Coord.from_global(pos, self.world)
				zone_index = pos.values[0]
				zone = self.world.cells.cell(zone_index)
				field_index = pos.values[1]
				field = zone.cells.cell(field_index)
			else:
				return (Void(), [], [], [])
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
		if coord:
			self._cached_coord = coord
		else:
			coord = self._cached_coord
		return coord
	def _get_player_data(self):
		if self._cached_player_pos is None:
			player, self._cached_player_pos = next(((monster, coord) for coord, monster in self.all_monsters(raw=True) if isinstance(monster, Player)), (None, self._cached_player_pos))
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
		for coord, monster in self.all_monsters(raw=True, zone_range=[expected_zone_index]):
			if isinstance(monster, Player):
				self._cached_player_pos = coord
				return monster, self._cached_player_pos
		# Not found in the last remembered zone.
		# Checking adjacent zones:
		adjacent_zones = set(iter_rect(
			expected_zone_index - Point(1, 1),
			expected_zone_index + Point(1, 1),
			)) - {expected_zone_index}
		for coord, monster in self.all_monsters(raw=True, zone_range=adjacent_zones):
			if isinstance(monster, Player):
				self._cached_player_pos = coord
				return monster, self._cached_player_pos
		# Not found in adjacent zones.
		# Performing full lookup:
		player, self._cached_player_pos = next(((monster, coord) for coord, monster in self.all_monsters(raw=True) if isinstance(monster, Player)), (None, None))
		return player, self._cached_player_pos

	def get_global_pos(self, actor):
		if actor == self.get_player():
			actor_coord = self.get_player_coord()
		else:
			actor_coord = actor.coord
		return actor_coord.get_global(self.world)
	def can_move(self, actor, pos):
		dest_pos = NestedGrid.Coord.from_global(pos, self.world)
		dest_cell = self.world.cell(dest_pos)
		return dest_cell.passable
	def transfer_actor(self, actor, pos):
		dest_pos = NestedGrid.Coord.from_global(pos, self.world)
		if actor == self.get_player():
			actor_coord = self.get_player_coord()
		else:
			actor_coord = actor.coord
		current_field_data = self.world.get_data(actor_coord)[-1]
		dest_field_data = self.world.get_data(dest_pos)[-1]
		if current_field_data != dest_field_data:
			current_field_data.monsters.remove(actor)
			dest_field_data.monsters.append(actor)
		actor.pos = dest_pos.values[-1]
	def iter_items_at(self, pos):
		if isinstance(pos, Point):
			pos = NestedGrid.Coord.from_global(pos, self.world)
		zone_items = self.world.get_data(pos)[-1].items
		for item_pos, item in zone_items:
			if pos.values[-1] == item_pos:
				yield item
	def iter_actors_at(self, pos, with_player=False):
		if isinstance(pos, Point):
			pos = NestedGrid.Coord.from_global(pos, self.world)
		zone_actors = self.world.get_data(pos)[-1].monsters
		for actor in zone_actors:
			if not with_player and isinstance(actor, Player):
				continue
			if pos.values[-1] == actor.pos:
				yield actor
	def all_monsters(self, raw=False, zone_range=None):
		for zone_index in (zone_range or self.world.cells):
			zone = self.world.cells.cell(zone_index)
			if zone is None:
				continue
			for field_index in zone.cells:
				for monster in zone.cells.cell(field_index).data.monsters:
					coord = NestedGrid.Coord(zone_index, field_index, monster.pos)
					if not raw:
						coord = coord.get_global(self.world)
					yield coord, monster
	def iter_actors_in_rect(self, rect):
		monster_zone_topleft = NestedGrid.Coord.from_global(rect.topleft, self.world)
		monster_zone_bottomright = NestedGrid.Coord.from_global(rect.bottomright, self.world)
		monster_zone_range = iter_rect(monster_zone_topleft.values[0], monster_zone_bottomright.values[0])
		for monster_coord, monster in self.all_monsters(raw=True, zone_range=monster_zone_range):
			monster_pos = monster_coord.get_global(self.world)
			if not rect.contains(monster_pos, with_border=True):
				continue
			monster.coord = monster_coord
			yield monster
	def iter_active_monsters(self):
		player_pos = self.get_player_coord().get_global(self.world)
		monster_action_range = Rect(
				player_pos - Point(MAX_MONSTER_ACTION_LENGTH, MAX_MONSTER_ACTION_LENGTH),
				Size(1 + MAX_MONSTER_ACTION_LENGTH * 2, 1 + MAX_MONSTER_ACTION_LENGTH * 2),
				)
		for monster in self.iter_actors_in_rect(monster_action_range):
			yield monster

def iter_rect(topleft, bottomright):
	for x in range(topleft.x, bottomright.x + 1):
		for y in range(topleft.y, bottomright.y + 1):
			yield Point(x, y)

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
			game.generate(None)

	main_game = MainGameMode(game)
	loop = clckwrkbdgr.tui.ModeLoop(ui)
	loop.run(main_game)
	if not game.is_finished():
		with savefile.save(SAVEFILE_VERSION) as writer:
			game.save(writer)
	else:
		savefile.unlink()

class MainGameMode(ui.MainGame):
	INDICATORS = [
			ui.Indicator((62, 0), 18, lambda self: "@{0:02X}.{1:X}.{2:X};{3:02X}.{4:X}.{5:X}".format(
				self.game.scene.get_player_coord().values[0].x,
				self.game.scene.get_player_coord().values[1].x,
				self.game.scene.get_player_coord().values[2].x,
				self.game.scene.get_player_coord().values[0].y,
				self.game.scene.get_player_coord().values[1].y,
				self.game.scene.get_player_coord().values[2].y,
				)),
			ui.Indicator((62, 1), 18, lambda self:"T:{0}".format(self.game.playing_time)),
			ui.Indicator((62, 2), 18, lambda self:"hp:{0}/{1}".format(self.game.scene.get_player().hp, self.game.scene.get_player().max_hp) if self.game.scene.get_player() else ""),
			ui.Indicator((62, 3), 18, lambda self:"inv:{0}".format(len(self.game.scene.get_player().inventory)) if self.game.scene.get_player() else ""),
			ui.Indicator((62, 4), 18, lambda self:"here:{0}".format(self.item_here().sprite.sprite) if self.item_here() else ""),
			]
	def __init__(self, game):
		super(MainGameMode, self).__init__(game)
		self.viewport = Rect((0, 0), (61, 23))
		self.center = Point(*(self.viewport.size // 2))
		self.centered_viewport = Rect((-self.center.x, -self.center.y), self.viewport.size)
	def get_viewrect(self):
		return Rect(
				self.game.scene.get_player_coord().get_global(self.game.scene.world) + self.centered_viewport.topleft,
				self.centered_viewport.size,
				)
	def item_here(self):
		return next(self.game.scene.iter_items_at(self.game.scene.get_player_coord()), None)
	def get_message_line_rect(self):
		return Rect(Point(0, 23), Size(80, 1))
	@ui.MainGame.Keys.bind('C')
	def char(self):
		game = self.game
		player_pos = game.scene.get_player_coord().get_global(game.scene.world)
		if True:
			npcs = [
					monster for monster_pos, monster
					in self.game.scene.all_monsters()
					if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1
					and isinstance(monster, Dweller)
					]
			questing = [
					npc for _, npc in self.game.scene.all_monsters()
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
						have_required_items = list(
								game.scene.get_player().iter_items(ColoredSkin, name=required_name),
								)[:required_amount]
						if len(have_required_items) >= required_amount:
							def _on_yes():
								self.game.fire_event(ChatThanks())
								for item in have_required_items:
									game.scene.get_player().drop(item)
								if game.scene.get_player().hp == game.scene.get_player().max_hp:
									game.scene.get_player().hp += bounty
								game.scene.get_player()._max_hp += bounty
								npc.quest = None
							def _on_no():
								self.game.fire_event(ChatComeLater())
							return TradeDialogMode('"You have {0} {1}. Trade it for +{2} max hp?" (y/n)'.format(*(npc.quest)),
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
	@ui.MainGame.Keys.bind('q')
	def show_questlog(self):
		game = self.game
		if True:
			questing = [
					(coord, npc) for coord, npc in self.game.scene.all_monsters(raw=True)
					if isinstance(npc, Dweller)
					and npc.quest
					]
			quest_log = QuestLog(questing)
			return quest_log

DirectionKeys = clckwrkbdgr.tui.Keymapping()
class DirectionDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DirectionKeys
	def __init__(self, on_direction=None):
		self.on_direction = on_direction
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, "Too crowded. Chat in which direction?")
	@DirectionKeys.bind(list('hjklyubn'), lambda key:UI.DIRECTION[str(key)])
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
