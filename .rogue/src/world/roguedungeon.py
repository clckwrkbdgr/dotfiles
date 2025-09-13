import functools
if not hasattr(functools, 'lru_cache'): # pragma: no cover -- py2
	functools.lru_cache = lambda: (lambda f:f)
from collections import namedtuple
from clckwrkbdgr.collections import dotdict
from clckwrkbdgr.math import Point, Rect, Matrix, Size
from clckwrkbdgr.pcg import RNG
import clckwrkbdgr.math
from ..engine import math, vision
import logging
trace = logging.getLogger('rogue')
import clckwrkbdgr.logging
from ..engine import scene, builders
from ..engine import actors, items, appliances, terrain

class Builder(builders.Builder):
	def get_item_distribution(self, depth): # pragma: no cover
		raise NotImplementedError()
	def get_monster_distribution(self, depth): # pragma: no cover
		raise NotImplementedError()

	def __init__(self, depth, is_bottom, *args, **kwargs):
		self.depth = depth
		self.is_bottom = is_bottom
		super(Builder, self).__init__(*args, **kwargs)
	def fill_grid(self, grid):
		self.dungeon = clckwrkbdgr.pcg.rogue.Dungeon(self.rng, self.size, Size(3, 3), Size(4, 4))
		self.dungeon.generate_rooms()
		self.dungeon.generate_maze()
		self.dungeon.generate_tunnels()
		grid.clear('void')
		grid.set_cell((0, 1), 'corner')
		grid.set_cell((0, 2), 'wall_v')
		grid.set_cell((0, 3), 'wall_h')
		grid.set_cell((0, 4), 'floor')
		grid.set_cell((0, 5), 'tunnel')
		grid.set_cell((0, 6), 'rogue_door')
	def generate_appliances(self):
		self.enter_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
		enter_room = self.dungeon.grid.cell(self.enter_room_key)
		if self.depth == 0:
			yield (self.point_in_rect(enter_room), 'dungeon_enter')
		else:
			yield (self.point_in_rect(enter_room), 'enter', 'rogue/{0}'.format(self.depth - 1))

		for _ in range(9):
			exit_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
			self.exit_room = self.dungeon.grid.cell(exit_room_key)
			if exit_room_key == self.enter_room_key:
				continue
		if not self.is_bottom:
			yield (self.point_in_rect(self.exit_room), 'exit', 'rogue/{0}'.format(self.depth + 1))

	def generate_items(self):
		item_distribution = [(prob, (item_type.__name__,)) for (prob, item_type) in self.get_item_distribution(self.depth)]
		for pos, item in self.distribute(builders.WeightedDistribution, item_distribution, self.amount_fixed(2, 4)
			):
			if item is None: # pragma: no cover
				continue
			room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
			room = self.dungeon.grid.cell(room_key)
			pos = self.point_in_rect(room)
			yield pos, item
		if self.is_bottom:
			yield (self.point_in_rect(self.exit_room), 'mcguffin')
	def generate_actors(self):
		monster_distribution = [(_, (monster_type.__name__,)) for (_, monster_type) in self.get_monster_distribution(self.depth)]
		available_rooms = [room for room in self.dungeon.grid.keys() if room != self.enter_room_key]
		for pos, monster in self.distribute(builders.WeightedDistribution, monster_distribution,  self.amount_fixed(5)):
			if monster is None: # pragma: no cover
				continue
			room = self.dungeon.grid.cell(self.rng.choice(available_rooms))
			pos = self.point_in_rect(room)
			yield pos, monster

class Scene(scene.Scene):
	""" Original Rogue-like map with grid of rectangular rooms connected by tunnels.
	Items, monsters, fitment objects are supplied.
	"""
	MAX_LEVELS = None
	SIZE = None
	BUILDER = None
	Room = Rect
	Tunnel = clckwrkbdgr.math.geometry.RectConnection

	def __init__(self, rng=None): # pragma: no cover
		self.size = None
		self.rooms = Matrix( (3, 3) )
		self.tunnels = []
		self.items = []
		self.monsters = []
		self.objects = []
		self.rng = rng or RNG()
	def generate(self, level_id):
		depth = int(level_id.split('/')[-1])
		if depth < 0 or depth >= self.MAX_LEVELS:
			raise KeyError("Invalid level ID: {0} (supports only [0; {1}))".format(level_id, self.MAX_LEVELS))
		is_bottom = depth >= (self.MAX_LEVELS - 1)

		builder = self.BUILDER(depth, is_bottom, self.rng, self.SIZE)
		builder.generate()
		self.size = self.SIZE
		self.rooms = builder.dungeon.grid
		self.tunnels = builder.dungeon.tunnels
		self.terrain = builder.make_grid()
		self.objects = list(builder.make_appliances())
		self.items = list(builder.make_items())
		self.monsters = list(builder.make_actors())
		#monster.fill_drops(self.rng)
	def make_vision(self, actor):
		if isinstance(actor, actors.Player):
			return Vision(self)
		return MonsterVision(self)
	def exit_actor(self, actor):
		self.monsters.remove(actor)
		return actor
	def enter_actor(self, actor, location):
		location = location or 'enter'
		stairs = next((pos for pos, obj in reversed(self.objects) if isinstance(obj, appliances.LevelPassage) and obj.id == location), None)
		assert stairs is not None, "No stairs with id {0}".format(repr(location))
		actor.pos = stairs
		self.monsters.append(actor)
	def rip(self, actor):
		for item in actor.drop_all():
			self.items.append(item)
			yield item.item
		self.monsters.remove(actor)
	def drop_item(self, item_at_pos):
		self.items.append(item_at_pos)
	def take_item(self, item_at_pos):
		found = next(_ for _ in self.items if _ == item_at_pos)
		self.items.remove(found)
		return found.item
	def get_area_rect(self):
		return Rect((0, 0),self.size)
	def valid(self, pos): # pragma: no cover -- TODO
		return 0 <= pos.x < self.size.width and 0 <= pos.y < self.size.height
	@functools.lru_cache()
	def room_of(self, pos):
		return next((room for room in self.rooms.data if room.contains(pos, with_border=True)), None)
	@functools.lru_cache()
	def tunnel_of(self, pos):
		return next((tunnel for tunnel in self.tunnels if tunnel.contains(pos)), None)
	@functools.lru_cache()
	def index_room_of(self, pos):
		return next((key for key in self.rooms.keys() if self.rooms.cell(key).contains(pos, with_border=True)), None)
	@functools.lru_cache()
	def get_tunnels(self, room):
		""" Returns all tunnels connected to the room. """
		tunnels = []
		for tunnel in self.tunnels:
			if room.contains(tunnel.start, with_border=True):
				tunnels.append(tunnel)
			elif room.contains(tunnel.stop, with_border=True):
				tunnels.append(tunnel)
		return tunnels
	@functools.lru_cache()
	def get_tunnel_rooms(self, tunnel):
		""" Returns both rooms that tunnel connects. """
		start_room = next(_ for _ in self.rooms.values() if _.contains(tunnel.start, with_border=True))
		stop_room = next(_ for _ in self.rooms.values() if _.contains(tunnel.stop, with_border=True))
		return start_room, stop_room
	def can_move(self, actor, pos):
		""" Returns True if pos is available for movement.
		If with_tunnels is False, prohibits movements in tunnels and their doors.
		If from_pos is given, considers relative direction and prohibits
		diagonal movement in/from/to tunnels.
		"""
		with_tunnels = (actor == self.get_player())
		from_pos = actor.pos
		dest_room = self.room_of(pos)
		if dest_room:
			if dest_room.contains(pos):
				return True
			for tunnel in self.get_tunnels(dest_room):
				if tunnel.contains(pos):
					if from_pos and math.is_diagonal(from_pos - pos):
						return False
					return True
		if with_tunnels:
			dest_tunnel = self.tunnel_of(pos)
			if dest_tunnel:
				if from_pos and math.is_diagonal(from_pos - pos):
					return False
				return True
		return False
	def _get_terrain_name(self, pos):
		pos = Point(pos.y, pos.x)
		for tunnel in self.tunnels:
			if pos == (tunnel.start.y, tunnel.start.x): return "door"
			if pos == (tunnel.stop.y, tunnel.stop.x): return "door"
			for cell in tunnel.iter_points():
				if pos == (cell.y, cell.x): return "tunnel"
		for room in self.rooms.values():
			if pos == (room.top, room.left): return "corner"
			if pos == (room.bottom, room.left): return "corner"
			if pos == (room.top, room.right): return "corner"
			if pos == (room.bottom, room.right): return "corner"
			for x in range(room.left+1, room.right):
				if pos == (room.top, x): return "wall_h"
				if pos == (room.bottom, x): return "wall_h"
			for y in range(room.top+1, room.bottom):
				if pos == (y, room.left): return "wall_v"
				if pos == (y, room.right): return "wall_v"
			for y in range(room.top+1, room.bottom):
				for x in range(room.left+1, room.right):
					if pos == (y, x): return 'floor'
		return 'void'
	def _get_terrain(self, pos):
		terrain = self._get_terrain_name(pos)
		return self.terrain.cell((0, {
			'void':  0,
			'corner':1,
			'wall_v':2,
			'wall_h':3,
			'floor': 4,
			'tunnel':5,
			'door'  :6,
			}[terrain]))
	def get_cell_info(self, pos):
		pos = Point(pos)
		return (
				self._get_terrain(pos),
				list(self.iter_appliances_at(pos)),
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)

	def __setstate__(self, data): # pragma: no cover -- TODO
		self.rooms = data.rooms
		self.tunnels = data.tunnels

		self.objects = data.objects
		self.items = data.map_items
		self.monsters = data.monsters
	def __getstate__(self): # pragma: no cover -- TODO
		data = dotdict()
		data.rooms = self.rooms
		data.tunnels = self.tunnels
		data.objects = self.objects
		data.map_items = []
		for pos, item in self.items:
			data.map_items.append( [pos, item] )
		data.monsters = self.monsters
		return data
	def save(self, stream): # pragma: no cover -- TODO
		for tile_index in self.rooms:
			tile = self.rooms.cell(tile_index)
			stream.write(tile.topleft.x)
			stream.write(tile.topleft.y)
			stream.write(tile.size.width)
			stream.write(tile.size.height)

		stream.write(len(self.tunnels))
		for tunnel in self.tunnels:
			stream.write(tunnel.start.x)
			stream.write(tunnel.start.y)
			stream.write(tunnel.stop.x)
			stream.write(tunnel.stop.y)
			stream.write(tunnel.direction)
			stream.write(tunnel.bending_point)

		for i in range(7):
			self.terrain.cell((0, i)).save(stream)

		stream.write(len(self.items))
		for item in self.items:
			item.save(stream)

		stream.write(len(self.monsters))
		for monster in self.monsters:
			monster.save(stream)

		stream.write(len(self.objects))
		for obj in self.objects:
			obj.save(stream)
	def load(self, stream): # pragma: no cover -- TODO
		super(Scene, self).load(stream)
		self.size = self.SIZE
		for tile_index in self.rooms:
			self.rooms.set_cell(tile_index, Rect(
				(stream.read(int), stream.read(int)),
				(stream.read(int), stream.read(int)),
				))

		tunnels = stream.read(int)
		for tunnel in range(tunnels):
			self.tunnels.append(self.Tunnel(
				Point(stream.read(int), stream.read(int)),
				Point(stream.read(int), stream.read(int)),
				stream.read(),
				stream.read(int),
				))

		self.terrain = Matrix((1, 7), None)
		for i in range(7):
			self.terrain.set_cell(Point(0, i), stream.read(terrain.Terrain))

		_items = stream.read(int)
		for _ in range(_items):
			self.items.append(stream.read(items.ItemAtPos))

		monsters = stream.read(int)
		for _ in range(monsters):
			self.monsters.append(actors.Actor.load(stream))

		objects = stream.read(int)
		for _ in range(objects):
			self.objects.append(stream.read(appliances.ObjectAtPos))

	@property
	def current_room(self):
		return self.room_of(self.get_player().pos)
	@property
	def current_tunnel(self):
		return self.tunnel_of(self.get_player().pos)
	def iter_cells(self, view_rect):
		trace.debug(list(self.rooms.keys()))
		for y in range(view_rect.topleft.y, view_rect.bottomright.y + 1):
			for x in range(view_rect.topleft.x, view_rect.bottomright.x + 1):
				pos = Point(x, y)
				terrain = self._get_terrain(pos)
				objects = list(self.iter_appliances_at(pos))
				items = list(self.iter_items_at(pos))
				monsters = list(self.iter_actors_at(pos, with_player=True))
				yield pos, (terrain, objects, items, monsters)
	def iter_items_at(self, pos):
		""" Yield items at pos in reverse order (from top to bottom). """
		for item_pos, item in reversed(self.items):
			if item_pos == pos:
				yield item
	def iter_actors_at(self, pos, with_player=False):
		""" Yield monsters at pos in reverse order (from top to bottom). """
		for monster in reversed(self.monsters):
			if not with_player and isinstance(monster, actors.Player):
				continue
			if monster.pos == pos:
				yield monster
	def iter_actors_in_rect(self, rect):
		for monster in self.monsters:
			if not rect.contains(monster.pos, with_border=True):
				continue
			yield monster
	def iter_appliances_at(self, pos):
		""" Yield objects at pos in reverse order (from top to bottom). """
		for obj_pos, obj in reversed(self.objects):
			if obj_pos == pos:
				yield obj
	def get_player(self):
		return next((monster for monster in self.monsters if isinstance(monster, actors.Player)), None)
	def iter_active_monsters(self):
		return self.monsters

class MonsterVision(vision.Vision):
	def __init__(self, scene):
		super(MonsterVision, self).__init__(scene)
		self.monster = None
	def is_visible(self, pos):
		if clckwrkbdgr.math.distance(self.monster.pos, pos) <= 1:
			return True
		return self.scene.room_of(self.monster.pos) == self.scene.room_of(pos)
	def visit(self, monster):
		self.monster = monster

class Vision(vision.Vision):
	def __init__(self, scene):
		super(Vision, self).__init__(scene)
		self.visited_rooms = Matrix((3, 3), False)
		self.visited_tunnels = [set() for tunnel in scene.tunnels]
	def save(self, stream): # pragma: no cover -- TODO
		stream.write(self.visited_rooms.width)
		stream.write(self.visited_rooms.height)
		for tile_index in self.visited_rooms:
			stream.write(self.visited_rooms.cell(tile_index))

		stream.write(len(self.visited_tunnels))
		for tunnel in self.visited_tunnels:
			stream.write(len(tunnel))
			for p in tunnel:
				stream.write(p.x)
				stream.write(p.y)
	def load(self, stream): # pragma: no cover -- TODO
		size = Size(stream.read(int), stream.read(int))
		self.visited_rooms = Matrix(size, None)
		for tile_index in self.visited_rooms:
			self.visited_rooms.set_cell(tile_index, bool(stream.read(int)))

		length = stream.read(int)
		self.visited_tunnels = []
		for _ in range(length):
			tunnel_length = stream.read(int)
			tunnel = set()
			for p in range(tunnel_length):
				tunnel.add(Point(stream.read(int), stream.read(int)))
			self.visited_tunnels.append(tunnel)
	def is_visible(self, obj, additional=None):
		""" Returns true if object (Room, Tunnel, Point) is visible for player.
		Additional data depends on type of primary object.
		Currently only Tunnel Points are considered.
		"""
		scene = self.scene
		if isinstance(obj, Scene.Room):
			return obj == scene.current_room
		if isinstance(obj, Scene.Tunnel):
			tunnel_visited = scene.tunnels.index(obj)
			tunnel_visited = self.visited_tunnels[tunnel_visited]
			return additional in tunnel_visited
		if isinstance(obj, Point):
			for room in scene.rooms.values():
				if room.contains(obj, with_border=True) and self.is_visible(room):
					return True
			for tunnel in scene.tunnels:
				if self.is_visible(tunnel, obj):
					return True
		return False
	def iter_important(self): # pragma: no cover
		if not self.scene.current_room:
			return
		for _ in self.scene.iter_actors_in_rect(self.scene.current_room):
			if _ != self.scene.get_player():
				yield _
	def is_explored(self, obj, additional=None):
		""" Returns true if object (Room, Tunnel, Point) was visible for player at some point and now can be remembered.
		Additional data depends on type of primary object.
		Currently only Tunnel Points are considered.
		"""
		scene = self.scene
		if isinstance(obj, Scene.Room):
			room_index = scene.index_room_of(obj.topleft)
			return self.visited_rooms.cell(room_index)
		if isinstance(obj, Scene.Tunnel):
			tunnel_visited = scene.tunnels.index(obj)
			tunnel_visited = self.visited_tunnels[tunnel_visited]
			return additional in tunnel_visited
		if isinstance(obj, Point):
			for room in scene.rooms.values():
				if room.contains(obj, with_border=True) and self.is_explored(room):
					return True
			for tunnel in scene.tunnels:
				if self.is_explored(tunnel, obj): # pragma: no covered -- TODO
					return True
		return False
	def visit_tunnel(self, tunnel, tunnel_index, pos, adjacent=True):
		""" Marks cell as visited. If adjacent is True, marks all neighbouring cells too. """
		shifts = [Point(0, 0)]
		if adjacent:
			shifts += [
				Point(-1, 0),
				Point(0, -1),
				Point(+1, 0),
				Point(0, +1),
				]
		tunnel_visited = self.visited_tunnels[tunnel_index]
		for shift in shifts:
			p = pos + shift
			if tunnel.contains(p):
				tunnel_visited.add(p)
	def visit(self, monster):
		""" Marks all objects (rooms, tunnels) related to pos as visited. """
		scene = self.scene
		pos = monster.pos
		room = scene.room_of(pos)
		if room:
			room_index = scene.index_room_of(pos)
			self.visited_rooms.set_cell(room_index, True)
			for tunnel in scene.get_tunnels(room):
				tunnel_index = scene.tunnels.index(tunnel)
				if room.contains(tunnel.start, with_border=True):
					self.visit_tunnel(tunnel, tunnel_index, tunnel.start, adjacent=False)
				if room.contains(tunnel.stop, with_border=True):
					self.visit_tunnel(tunnel, tunnel_index, tunnel.stop, adjacent=False)
		tunnel = scene.tunnel_of(pos)
		if tunnel:
			tunnel_index = scene.tunnels.index(tunnel)
			self.visit_tunnel(tunnel, tunnel_index, pos)
		return []
