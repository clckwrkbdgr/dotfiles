import copy
import logging
Log = logging.getLogger(__name__)
from ..math import Point, Size, Matrix, Rect
from ..math.geometry import RectConnection
"""
Original Rogue's dungeon: grid or rooms connected by straight tunnels.
"""

class Dungeon(object):
	def __init__(self, rng, size, grid_size, min_room_size, room_margin=None):
		self.size = size
		self.grid_size = Size(grid_size)
		self.min_room_size = Size(min_room_size)
		self.margin = Size(room_margin or Size(1, 1))
		self.rng = rng
		self.original_rng_seed = rng.value

		self.grid = Matrix(grid_size)
		self.cell_size = Size(self.size.width // self.grid_size.width, self.size.height // self.grid_size.height)
		self.max_room_size = Size(
				max(self.min_room_size.width, self.cell_size.width - self.margin.width * 2),
				max(self.min_room_size.height, self.cell_size.height - self.margin.height * 2),
				)
	def iter_rooms(self):
		for room in self.grid.size.iter_points():
			yield self.grid.cell(room)
	def iter_tunnels(self):
		for tunnel in self.tunnels:
			yield tunnel
	def generate_rooms(self):
		for cell in self.grid.size.iter_points():
			room_size = Size(
					self.rng.range(self.min_room_size.width, self.max_room_size.width + 1),
					self.rng.range(self.min_room_size.height, self.max_room_size.height + 1),
					)
			topleft = Point(cell.x * self.cell_size.width, cell.y * self.cell_size.height)
			random_non_negative = lambda _:self.rng.range(_) if _ > 0 else 0
			topleft += Point(
					random_non_negative(self.cell_size.width - room_size.width - 1),
					random_non_negative(self.cell_size.height - room_size.height - 1),
					)
			self.grid.set_cell(cell, Rect(topleft, room_size))
	def generate_maze(self):
		self.maze = {k:set() for k in self.grid.size.iter_points()}
		for column in range(self.grid.size.width):
			for row in range(self.grid.size.height):
				if column < self.grid.size.width - 1:
					a, b = Point(column, row), Point(column + 1, row)
					self.maze[a].add(b)
					self.maze[b].add(a)
				if row < self.grid.size.height - 1:
					a, b = Point(column, row), Point(column, row + 1)
					self.maze[a].add(b)
					self.maze[b].add(a)
		for i in range(5):
			new_config = copy.deepcopy(self.maze)
			all_links = set(tuple(sorted((node_from, node_to))) for node_from in self.maze for node_to in self.maze[node_from])
			removed = self.rng.choice(sorted(all_links))
			node, other = removed
			if node in new_config and other in new_config[node]:
				new_config[node].remove(other)
			if other in new_config and node in new_config[other]:
				new_config[other].remove(node)

			all_links = set(tuple(sorted((node_from, node_to))) for node_from in new_config for node_to in new_config[node_from])
			clusters = []
			for a, b in all_links:
				new_clusters = [{a, b}]
				for cluster in clusters:
					for other in new_clusters:
						if cluster & other:
							other.update(cluster)
							break
					else:
						new_clusters.append(cluster)
				clusters = new_clusters
			for node in new_config.keys():
				if any(node in cluster for cluster in clusters):
					continue
				clusters.append({node})
			is_connected = len(clusters) == 1
			if is_connected:
				self.maze = new_config
	def generate_tunnels(self):
		self.tunnels = []
		all_links = set(tuple(sorted((node_from, node_to))) for node_from in self.maze for node_to in self.maze[node_from])
		for start_room, stop_room in sorted(all_links):
			assert abs(start_room.x - stop_room.x) + abs(start_room.y - stop_room.y) == 1
			if abs(start_room.x - stop_room.x) > 0:
				direction = 'H'
			else:
				direction = 'V'
			start_room = self.grid.cell(start_room)
			stop_room = self.grid.cell(stop_room)

			bending_point = 1
			if direction == 'H':
				assert start_room.topleft.x < stop_room.topleft.x, "Original RNG seed: {0}".format(self.original_rng_seed)
				start = Point(
					start_room.topleft.x + start_room.size.width,
					self.rng.range(start_room.topleft.y+1, start_room.topleft.y + stop_room.size.height),
					)
				stop = Point(
					stop_room.topleft.x,
					self.rng.range(stop_room.topleft.y+1, stop_room.topleft.y + stop_room.size.height),
					)
				if abs(stop_room.topleft.x - (start_room.topleft.x + start_room.size.width)) > 1:
					bending_point = self.rng.range(1, abs(stop_room.topleft.x - (start_room.topleft.x + start_room.size.width)))
			else:
				assert start_room.topleft.y < stop_room.topleft.y, "Original RNG seed: {0}".format(self.original_rng_seed)
				start = Point(
					self.rng.range(start_room.topleft.x+1, start_room.topleft.x+start_room.size.width),
					start_room.topleft.y + start_room.size.height,
					)
				stop = Point(
					self.rng.range(stop_room.topleft.x+1, stop_room.topleft.x+stop_room.size.width),
					stop_room.topleft.y,
					)
				if abs(stop_room.topleft.y - (start_room.topleft.y + start_room.size.height)) > 1:
					bending_point = self.rng.range(1, abs(stop_room.topleft.y - (start_room.topleft.y + start_room.size.height)))
			self.tunnels.append(RectConnection(
				start, stop, direction, bending_point,
				))
