import types, copy
try:
	SimpleNamespace = types.SimpleNamespace
except AttributeError: # pragma: no cover -- py2
	import argparse
	SimpleNamespace = argparse.Namespace

from clckwrkbdgr import pcg
from clckwrkbdgr import utils
from clckwrkbdgr.math import Point, Size, Matrix
import clckwrkbdgr.math.graph

class Generator: # pragma: no cover -- TODO relies on built-in module `random`. Needs mocks.
	def randint(self, max_value):
		return random.randrange(max_value)
	def randrange(self, min_value, max_value):
		return random.randrange(min_value, max_value)
	def choice(self, sequence):
		return random.choice(sequence)

	def pos_in_rect(self, rect, with_boundaries=False):
		shrink = 0 if with_boundaries else 1
		return Point(
				random.randrange(rect.left + shrink, rect.right + 1 - shrink),
				random.randrange(rect.top + shrink, rect.bottom + 1 - shrink),
				)
	def size(self, min_size, max_size):
		""" Boundaries are included. """
		min_size, max_size = map(Size, (min_size, max_size))
		return Size(
				random.randrange(min_size.width, max_size.width + 1),
				random.randrange(min_size.height, max_size.height + 1),
				)
	def point(self, x_max_range, y_max_range):
		""" Boundaries are NOT included. """
		return Point(
				random.randrange(x_max_range) if x_max_range > 0 else 0,
				random.randrange(y_max_range) if y_max_range > 0 else 0,
				)
	def weighted_choices(self, weights_and_items, amount=1):
		""" Makes random weighted choice based on list of tuples: (<weight>, <item>), ...
		Returns list of items.
		"""
		return pcg.weighted_choices(random, weights_and_items, k=amount)

	def distribute(self, distribution, min_amount, max_amount=None):
		""" Places objects generated from weighted distribution.
		Objects should be callables (either functions, or object types) with no arguments.
		If only min_amount is given, it is considered fixed amount.
		Yields results of calling objects except those that are None.
		"""
		if max_amount is not None:
			amount = self.randrange(min_amount, max_amount)
		else:
			amount = min_amount
		for object_type in self.weighted_choices(distribution, amount):
			if object_type is None:
				continue
			yield object_type()
	def distribute_in_rooms(self, distribution, rooms, min_amount, max_amount=None):
		""" Places objects generated from weighted distribution in random positions in random rooms.
		Objects should be callables (either functions, or object types) with no arguments.
		If only min_amount is given, it is considered fixed amount.
		Yields tuples (Point, <called result>).
		"""
		for constructed_object in self.distribute(distribution, min_amount, max_amount):
			room = self.choice(rooms)
			pos = self.pos_in_rect(room)
			yield (pos, constructed_object)
	def grid_of_rooms(self, room_class, map_size, grid_size, min_room_size, margin):
		""" Returns Matrix of grid_size with random sized and positioned Rooms
		within evenly spaced grid cells.
		Margin is a Size (width+height) from _both_ sides to leave space for tunnels (room walls included into room size).
		Min room size also includes walls.
		"""
		map_size, grid_size, min_room_size, margin = map(Size, (map_size, grid_size, min_room_size, margin))
		grid = Matrix(grid_size)
		cell_size = Size(map_size.width // grid_size.width, map_size.height // grid_size.height)
		max_room_size = cell_size - margin * 2
		if max_room_size.width < min_room_size.width:
			max_room_size.width = min_room_size.width
		if max_room_size.height < min_room_size.height:
			max_room_size.height = min_room_size.height
		for cell in grid:
			room_size = self.size(min_room_size, max_room_size)
			topleft = Point(cell.x * cell_size.width, cell.y * cell_size.height)
			topleft += self.point(
					cell_size.width - room_size.width - 1,
					cell_size.height - room_size.height - 1,
					)
			grid.set_cell(cell, room_class(topleft, room_size))
		return grid
	def tunnel(self, tunnel_class, start_room, stop_room, direction):
		""" Generates tunnel between rooms.
		Assumes that they are not intersecting and there is
		at least 1 cell space between them.
		Direction of tunnel should correspond to relative placement
		of rooms, otherwise behaviour is undefined.
		"""
		bending_point = 1
		if direction == 'H':
			if start_room.left > stop_room.left:
				start_room, stop_room = stop_room, start_room
			start = Point(
				start_room.right,
				self.randrange(start_room.top+1, start_room.bottom),
				)
			stop = Point(
				stop_room.left,
				self.randrange(stop_room.top+1, stop_room.bottom),
				)
			if abs(stop_room.left - start_room.right) > 1:
				bending_point = self.randrange(1, abs(stop_room.left - start_room.right))
		else:
			if start_room.top > stop_room.top:
				start_room, stop_room = stop_room, start_room
			start = Point(
				self.randrange(start_room.left+1, start_room.right),
				start_room.bottom,
				)
			stop = Point(
				self.randrange(stop_room.left+1, stop_room.right),
				stop_room.top,
				)
			if abs(stop_room.top - start_room.bottom) > 1:
				bending_point = self.randrange(1, abs(stop_room.top - start_room.bottom))
		return tunnel_class(
			start=start,
			stop=stop,
			direction=direction,
			bending_point=bending_point,
			)
	def grid_of_tunnels(self, tunnel_class, grid, linked_rooms):
		""" Returns list of Tunnels randomly put between specified linked rooms
		of a grid of Rooms.
		Each point in link should be actual Point (in grid).
		"""
		tunnels = []
		for start_room, stop_room in linked_rooms:
			assert abs(start_room.x - stop_room.x) + abs(start_room.y - stop_room.y) == 1
			if abs(start_room.x - stop_room.x) > 0:
				direction = 'H'
			else:
				direction = 'V'
			tunnels.append(self.tunnel(tunnel_class, grid.cell(start_room), grid.cell(stop_room), direction))
		return tunnels
	def original_rogue_dungeon(self, map_size, grid_size,
			room_class, tunnel_class,
			item_distribution, item_amount,
			monster_distribution, monster_amount,
			prev_level_id=None, next_level_id=None,
			exit_connected_id=None, enter_connected_id=None,
			enter_object_type=None, exit_object_type=None,
			item_instead_of_exit=None,
			max_tunnel_etching_tries=5,
			):
		""" Generates original Rogue dungeon level.
		Grid of rectangular rooms linked by tunnels to form a simple maze.
		Level will have enter and exit stairs (as Furniture objects, exact types should be supplied as enter_object_type and exit_object_type and should be callable, accepting corresponding level id + connected entry id on the other side).
		If item_insted_of_exit specified, it should be a type, there will be no exit object and additional item will be added to the list of items on level.
		Item and monster distributions should be in format for Generator.distribute().
		Amounts are either tuples (min, max) or exact integer amount.
		Returns namespace with fields:
		- rooms - Matrix of Rooms;
		- tunnels - list of Tunnels;
		- objects = list of pairs (Point, Furniture);
		- items - list of pairs (Point, Item);
		- monsters - list of Monsters.
		"""
		result = SimpleNamespace()
		result.rooms = self.grid_of_rooms(room_class,
				map_size, grid_size, min_room_size=(4, 4), margin=(1, 1),
				)
		maze = clckwrkbdgr.math.graph.grid_from_matrix(result.rooms)
		for i in range(max_tunnel_etching_tries):
			new_config = copy.copy(maze)
			removed = self.choice(list(maze.all_links()))
			new_config.disconnect(*removed)
			if clckwrkbdgr.math.graph.is_connected(new_config):
				maze = new_config
		result.tunnels = self.grid_of_tunnels(tunnel_class, result.rooms, maze.all_links())

		result.objects = []

		enter_room_key = self.choice(list(result.rooms.keys()))
		enter_room = result.rooms.cell(enter_room_key)
		if enter_object_type is not None:
			result.objects.append( (self.pos_in_rect(enter_room), enter_object_type(prev_level_id, enter_connected_id)) )

		exit_room_key = self.choice(list(set(result.rooms.keys()) - {enter_room_key}))
		exit_room = result.rooms.cell(exit_room_key)
		exit_pos = self.pos_in_rect(exit_room)
		if exit_object_type is not None and not item_instead_of_exit:
			result.objects.append( (exit_pos, exit_object_type(next_level_id, exit_connected_id)) )

		if utils.is_collection(item_amount):
			min_item_amount, max_item_amount = item_amount
		else:
			min_item_amount, max_item_amount = item_amount, None
		result.items = list(self.distribute_in_rooms(
			item_distribution, list(result.rooms.values()),
			min_item_amount, max_item_amount,
			))

		if item_instead_of_exit:
			result.items.append( (exit_pos, item_instead_of_exit()) )

		if utils.is_collection(monster_amount):
			min_monster_amount, max_monster_amount = monster_amount
		else:
			min_monster_amount, max_monster_amount = monster_amount, None
		available_rooms = [room for room in result.rooms.values() if room != enter_room and room != exit_room]
		result.monsters = []
		for pos, monster in self.distribute_in_rooms(monster_distribution, available_rooms, min_monster_amount, max_monster_amount):
			monster.pos = pos
			drop_distributions = monster.drops
			if drop_distributions and drop_distributions[0] and not utils.is_collection(drop_distributions[0][0]):
				drop_distributions = [drop_distributions]
			for distribution in drop_distributions:
				monster.inventory.extend(self.distribute(distribution, 1))
			result.monsters.append(monster)
		return result
