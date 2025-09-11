import string
from collections import namedtuple
from clckwrkbdgr.math.grid import NestedGrid
import clckwrkbdgr.math
from clckwrkbdgr import utils
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr.math import Point, Rect, Size
from ..engine import builders, vision, scene
from ..engine.items import ItemAtPos
from ..engine.actors import Actor, Player
from ..engine.terrain import Terrain

class ZoneData(object):
	def save(self, stream):
		pass
	@classmethod
	def load(cls, stream):
		return cls()

class FieldData(object):
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
			self.items.append(stream.read(ItemAtPos))

		monsters = stream.read(int)
		for _ in range(monsters):
			self.monsters.append(Actor.load(stream))
		return self

Color = namedtuple('Color', 'dweller monster')
COLORS = {
			'red': Color(True, True),
			'green': Color(True, True),
			'blue': Color(True, True),
			'yellow': Color(True, True),
			'cyan': Color(True, True),
			'magenta': Color(True, True),
			'white': Color(True, True),
			'bold_black': Color(True, True),
			'bold_red': Color(True, True),
			'bold_green': Color(True, True),
			'bold_blue': Color(True, True),
			'bold_yellow': Color(True, True),
			'bold_cyan': Color(True, True),
			'bold_magenta': Color(True, True),
			'bold_white': Color(False, True),
			}

class Builder(builders.Builder):
	def fill_grid(self, grid):
		self._make_terrain(grid)
		self._building = self.rng.randrange(50) == 0
		if self._building:
			self._building = self._add_building(grid)
	def _add_building(self, grid):
		building = Rect(
				Point(2 + self.rng.randrange(3), 2 + self.rng.randrange(3)),
				Size(6 + self.rng.randrange(3), 6 + self.rng.randrange(3)),
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
		if self.rng.randrange(2) == 0:
			door = building.top + 1 + self.rng.randrange(building.height - 2)
			if self.rng.randrange(2) == 0:
				grid.set_cell((building.left, door), 'floor')
			else:
				grid.set_cell((building.right, door), 'floor')
		else:
			door = building.left + 1 + self.rng.randrange(building.width - 2)
			if self.rng.randrange(2) == 0:
				grid.set_cell((door, building.top), 'floor')
			else:
				grid.set_cell((door, building.bottom), 'floor')
		return building
	def generate_actors(self):
		if self._building:
			yield self._make_dweller(self._building)
			return
		monster_count = self.rng.randrange(5) if self.rng.randrange(5) == 0 else 0
		for _ in range(monster_count):
			yield self._make_monster(self.grid)
	def _make_dweller(self, building):
		dweller_pos = building.topleft + Point(1, 1) + Point(
				self.rng.randrange(building.width - 2),
				self.rng.randrange(building.height - 2),
				)
		colors = [name for name, color in sorted(COLORS.items()) if color.dweller]
		monster_color = self.rng.choice(colors)
		return dweller_pos, 'dweller', monster_color
	def _make_monster(self, grid):
		monster_pos = None
		while monster_pos is None or self.has_actor(monster_pos):
			monster_pos = Point(
					self.rng.randrange(grid.size.width),
					self.rng.randrange(grid.size.height),
					)
		colors = [name for name, color in sorted(COLORS.items()) if color.monster]
		normal_colors = [color for color in colors if not color.startswith('bold_')]
		bold_colors = [color for color in colors if color.startswith('bold_')]
		strong = self.rng.randrange(2)
		aggressive = self.rng.randrange(2)
		monster_color = self.rng.choice(bold_colors if aggressive else normal_colors)
		key = 'colored_monster_carrying' if self.rng.randrange(2) else 'colored_monster'
		return (
				monster_pos, key, 
				self.rng.choice(string.ascii_lowercase),
				monster_color, strong, aggressive,
				)

class Forest(Builder):
	def _make_terrain(self, grid):
		grid.clear('grass')
		forest_density = self.rng.randrange(10) * 10
		for _ in range(forest_density):
			grid.set_cell(self.point(), 'tree')
		for _ in range(10):
			grid.set_cell(self.point(), 'bush')
		for _ in range(10):
			grid.set_cell(self.point(), 'plant')

class Desert(Builder):
	def _make_terrain(self, grid):
		grid.clear('sand')
		for _ in range(self.rng.randrange(3)):
			grid.set_cell(self.point(), 'rock')
		for _ in range(10):
			grid.set_cell(self.point(), 'plant')

class Thundra(Builder):
	def _make_terrain(self, grid):
		grid.clear('snow')
		for _ in range(3 + self.rng.randrange(3)):
			grid.set_cell(self.point(), 'ice')
		for _ in range(3 + self.rng.randrange(7)):
			grid.set_cell(self.point(), 'frozen_ground')

class Marsh(Builder):
	def _make_terrain(self, grid):
		grid.clear('swamp')
		for _ in range(100):
			grid.set_cell(self.point(), 'bog')
		for _ in range(self.rng.randrange(100)):
			grid.set_cell(self.point(), 'grass')
		for _ in range(self.rng.randrange(5)):
			grid.set_cell(self.point(), 'swamp_tree')
		for _ in range(self.rng.randrange(10)):
			grid.set_cell(self.point(), 'dead_tree')

class Vision(vision.OmniVision):
	def __init__(self, scene):
		super(Vision, self).__init__(scene)
		self.visible_monsters = []
		self._first_visit = True
	def iter_important(self):
		for _ in self.visible_monsters:
			if _.is_hostile_to(self.scene.get_player()):
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
	MAX_MONSTER_ACTION_LENGTH = 10
	SIZE = [(256, 256), (16, 16), (16, 16)]

	def __init__(self, builders, rng=None):
		self.world = NestedGrid(self.SIZE, [None, ZoneData, FieldData], Terrain)
		self._cached_player_pos = None
		self.rng = rng or RNG()
		self.builders = builders
	@classmethod
	def get_autoexplorer_class(cls): # pragma: no cover -- TODO
		return auto.EndlessAreaExplorer
	def make_vision(self, actor):
		if isinstance(actor, Player):
			return Vision(self)
		return MonsterVision(self)
	def generate(self, id):
		zone_pos = Point(
				self.rng.randrange(self.world.cells.size.width),
				self.rng.randrange(self.world.cells.size.height),
				)
		zone = self.generate_zone(zone_pos)

		self._player_pos = NestedGrid.Coord(
				zone_pos,
				Point(
					self.rng.randrange(zone.cells.size.width),
					self.rng.randrange(zone.cells.size.height),
					),
				Point(
					self.rng.randrange(zone.sizes[-1].width),
					self.rng.randrange(zone.sizes[-1].width),
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
	def get_area_rect(self):
		return Rect((0, 0), Size(
			self.world.sizes[-3].width * self.world.sizes[-2].width * self.world.sizes[-1].width,
			self.world.sizes[-3].height * self.world.sizes[-2].height * self.world.sizes[-1].height,
			))
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
			builder_type = self.rng.choice(self.builders)
			builder = builder_type(self.rng, field.cells)
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
				if zone:
					field = zone.cells.cell(field_index)
			if field is None:
				return (None, [], [], [])
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
		else: # pragma: no cover -- TODO
			coord = self._cached_coord
		return coord
	def _get_player_data(self): # pragma: no cover -- TODO
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
		if actor == self.get_player(): # pragma: no cover -- TODO
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
				actor.coord = pos
				yield actor
	def all_monsters(self, raw=False, zone_range=None):
		for zone_index in (zone_range or self.world.cells):
			if not self.world.cells.valid(zone_index):
				continue
			zone = self.world.cells.cell(zone_index)
			if zone is None:
				continue
			for field_index in zone.cells:
				for monster in zone.cells.cell(field_index).data.monsters:
					coord = NestedGrid.Coord(zone_index, field_index, monster.pos)
					if not raw: # pragma: no cover -- TODO
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
				player_pos - Point(self.MAX_MONSTER_ACTION_LENGTH, self.MAX_MONSTER_ACTION_LENGTH),
				Size(1 + self.MAX_MONSTER_ACTION_LENGTH * 2, 1 + self.MAX_MONSTER_ACTION_LENGTH * 2),
				)
		for monster in self.iter_actors_in_rect(monster_action_range):
			yield monster

def iter_rect(topleft, bottomright):
	for x in range(topleft.x, bottomright.x + 1):
		for y in range(topleft.y, bottomright.y + 1):
			yield Point(x, y)
