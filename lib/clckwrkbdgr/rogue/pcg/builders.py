import itertools
import copy
from ..math import Matrix, Point, Size, Rect
from ..messages import Log
from . import _base as pcg

class Builder(object):
	def __init__(self, rng, map_size):
		self.rng = rng
		self.size = map_size
		self.strata = None
		self.original_rng_seed = rng.value
		self.start_pos = None
		self.exit_pos = None
	def build(self):
		self.strata = Matrix(self.size, None)
		self._build()
	def _build(self): # pragma: no cover
		raise NotImplementedError()

class RogueDungeon(Builder):
	def _build(self):
		grid_size = Size(3, 3)
		min_room_size = Size(4, 4)
		margin = Size(1, 1)
		grid = Matrix(grid_size)
		cell_size = Size(self.size.width // grid_size.width, self.size.height // grid_size.height)
		max_room_size = Size(
				cell_size.width - margin.width * 2,
				cell_size.height - margin.height * 2
				)
		if max_room_size.width < min_room_size.width:
			max_room_size = Size(min_room_size.width, max_room_size.height)
		if max_room_size.height < min_room_size.height:
			max_room_size = Size(max_room_size.width, min_room_size.height)
		for cell in grid.size:
			room_size = Size(
					self.rng.range(min_room_size.width, max_room_size.width + 1),
					self.rng.range(min_room_size.height, max_room_size.height + 1),
					)
			topleft = Point(cell.x * cell_size.width, cell.y * cell_size.height)
			random_non_negative = lambda _:self.rng.range(_) if _ > 0 else 0
			topleft += Point(
					random_non_negative(cell_size.width - room_size.width - 1),
					random_non_negative(cell_size.height - room_size.height - 1),
					)
			grid.set_cell(cell.x, cell.y, Rect(topleft, room_size))

		maze = {k:set() for k in grid.size}
		for column in range(grid.size.width):
			for row in range(grid.size.height):
				if column < grid.size.width - 1:
					a, b = Point(column, row), Point(column + 1, row)
					maze[a].add(b)
					maze[b].add(a)
				if row < grid.size.height - 1:
					a, b = Point(column, row), Point(column, row + 1)
					maze[a].add(b)
					maze[b].add(a)
		for i in range(5):
			new_config = copy.deepcopy(maze)
			all_links = set(tuple(sorted((node_from, node_to))) for node_from in maze for node_to in maze[node_from])
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
				maze = new_config

		tunnels = []
		all_links = set(tuple(sorted((node_from, node_to))) for node_from in maze for node_to in maze[node_from])
		for start_room, stop_room in sorted(all_links):
			assert abs(start_room.x - stop_room.x) + abs(start_room.y - stop_room.y) == 1
			if abs(start_room.x - stop_room.x) > 0:
				direction = 'H'
			else:
				direction = 'V'
			start_room = grid.cell(start_room.x, start_room.y)
			stop_room = grid.cell(stop_room.x, stop_room.y)

			bending_point = 1
			if direction == 'H':
				assert start_room.topleft.x < stop_room.topleft.x, "Original RNG seed: {0}".format(original_rng_seed)
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
				assert start_room.topleft.y < stop_room.topleft.y, "Original RNG seed: {0}".format(original_rng_seed)
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
			tunnels.append((
				start,
				stop,
				direction,
				bending_point,
				))

		for room in grid.size:
			room = grid.cell(room.x, room.y)
			self.strata.set_cell(room.topleft.x, room.topleft.y, 'corner')
			self.strata.set_cell(room.topleft.x, room.topleft.y+room.size.height, 'corner')
			self.strata.set_cell(room.topleft.x+room.size.width, room.topleft.y, 'corner')
			self.strata.set_cell(room.topleft.x+room.size.width, room.topleft.y+room.size.height, 'corner')
			for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
				self.strata.set_cell(x, room.topleft.y, 'wall_h')
				self.strata.set_cell(x, room.topleft.y+room.size.height, 'wall_h')
			for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
				self.strata.set_cell(room.topleft.x, y, 'wall_v')
				self.strata.set_cell(room.topleft.x+room.size.width, y, 'wall_v')
			for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
				for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
					self.strata.set_cell(x, y, 'floor')

		for start, stop, direction, bending_point in tunnels:
			iter_points = []
			if direction == 'H':
				lead = start.y
				for x in range(start.x, stop.x + 1):
					iter_points.append( Point(x, lead))
					if x == start.x + bending_point:
						if start.y < stop.y:
							for y in range(start.y + 1, stop.y + 1):
								iter_points.append( Point(x, y))
						else:
							for y in reversed(range(stop.y, start.y)):
								iter_points.append( Point(x, y))
						lead = stop.y
			else:
				lead = start.x
				for y in range(start.y, stop.y + 1):
					iter_points.append( Point(lead, y))
					if y == start.y + bending_point:
						if start.x < stop.x:
							for x in range(start.x + 1, stop.x + 1):
								iter_points.append( Point(x, y))
						else:
							for x in reversed(range(stop.x, start.x)):
								iter_points.append( Point(x, y))
						lead = stop.x
			for cell in iter_points:
				self.strata.set_cell(cell.x, cell.y, 'passage')
			self.strata.set_cell(start.x, start.y, 'door')
			self.strata.set_cell(stop.x, stop.y, 'door')

		enter_room_key = self.rng.choice(list(grid.size))
		enter_room = grid.cell(enter_room_key.x, enter_room_key.y)
		self.start_pos = Point(
					self.rng.range(enter_room.topleft.x + 1, enter_room.topleft.x + enter_room.size.width + 1 - 1),
					self.rng.range(enter_room.topleft.y + 1, enter_room.topleft.y + enter_room.size.height + 1 - 1),
					)

		for _ in range(9):
			exit_room_key = self.rng.choice(list(grid.size))
			exit_room = grid.cell(exit_room_key.x, exit_room_key.y)
			self.exit_pos = Point(
					self.rng.range(exit_room.topleft.x + 1, exit_room.topleft.x + exit_room.size.width + 1 - 1),
					self.rng.range(exit_room.topleft.y + 1, exit_room.topleft.y + exit_room.size.height + 1 - 1),
					)
			if exit_room_key != enter_room_key:
				break
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

class BinarySpacePartition(object):
	def __init__(self, rng, min_width=15, min_height=10):
		self.rng = rng
		self.min_size = (min_width, min_height)
		self._unfit_both_dimensions = False
	def set_unfit_both_dimensions(self, value):
		self._unfit_both_dimensions = bool(value)
	def door_generator(self, room): # pragma: no cover
		""" Takes a Rect object and generates random Point for door position inside it.
		No need to determine wall facing and location, the algorithm would decide automatically.
		By default door is generated in random manner.
		"""
		x = self.rng.range(room.topleft.x, room.topleft.x + room.size.width - 1)
		y = self.rng.range(room.topleft.y, room.topleft.y + room.size.height - 1)
		Log.debug("Generating door in {0}:  ({1}, {2})".format(room, x, y))
		return Point(x, y)
	def hor_ver_generator(self): # pragma: no cover
		""" Used to determine direction of the split for the current room.
		It should return True for horizontal and False for vertical room.
		By default these values are generated in random manner.
		"""
		return self.rng.choice([False, True])
	def generate(self, topleft, bottomright):
		""" Generates BS partition for given rectangle.
		Yield tuples (topleft, bottomright, is_horizontal, door).
		Tuples go from the biggest room to the all subrooms descending.
		Sibling rooms go left-to-right and top-to-bottom.
		"""
		Log.debug("topleft={0}, bottomright={1}".format(topleft, bottomright))
		too_narrow = abs(topleft.x - bottomright.x) <= self.min_size[0]
		too_low = abs(topleft.y - bottomright.y) <= self.min_size[1]
		unfit = False
		if self._unfit_both_dimensions:
			unfit = too_narrow or too_low
		else:
			unfit = too_narrow and too_low
		if unfit:
			return
		horizontal = False if too_narrow else (True if too_low else self.hor_ver_generator())
		new_topleft = Point(topleft.x + 2, topleft.y + 2)
		userspace = Rect(
				new_topleft,
				Size(
					bottomright.x - new_topleft.x + 1,
					bottomright.y - new_topleft.y + 1,
				))
		if userspace.size.width <= 0 or userspace.size.height <= 0:
			return
		assert userspace.size.width > 1 or userspace.size.height > 1
		if self._unfit_both_dimensions:
			for _ in range(userspace.size.width * userspace.size.height):
				door = self.door_generator(userspace)
				if horizontal:
					left_bound = userspace.topleft.x + self.min_size[0]
					right_bound = userspace.topleft.x + userspace.size.width - self.min_size[0]
					if not (left_bound <= door.x <= right_bound):
						continue
				else:
					top_bound = userspace.topleft.y + self.min_size[1]
					bottom_bound = userspace.topleft.y + userspace.size.height - self.min_size[1]
					if not (top_bound <= door.y <= bottom_bound):
						continue
				break
			else:
				return
		else:
			door = self.door_generator(userspace)
		assert userspace.contains(door), "Door {0} not in room user space {1}".format(door, userspace)
		yield (topleft, bottomright, horizontal, door)
		if horizontal:
			the_divide, door_pos = door
			for x in self.generate(topleft, Point(the_divide - 1, bottomright.y)):
				yield x
			for x in self.generate(Point(the_divide + 1, topleft.y), bottomright):
				yield x
		else:
			door_pos, the_divide = door
			for x in self.generate(topleft, Point(bottomright.x, the_divide - 1)):
				yield x
			for x in self.generate(Point(topleft.x, the_divide + 1), bottomright):
				yield x

class BSPBuilder(object):
	""" Fills specified field with binary space partition.
	Uses tuples generated by BinarySpacePartition.
	Draws a line with a 'door', overwrites all cell contents for specified rectangle.
	"""
	def __init__(self, field, free=False, obstacle=True, door=False):
		self.field = field
		self.free, self.obstacle, self.door = free, obstacle, door
	def fill(self, topleft, bottomright, is_horizontal, door_pos):
		for x in range(topleft.x, bottomright.x + 1):
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell(x, y, self.free())
		if is_horizontal:
			the_divide = door_pos.x
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell(the_divide, y, self.obstacle())
		else:
			the_divide = door_pos.y
			for x in range(topleft.x, bottomright.x + 1):
				self.field.set_cell(x, the_divide, self.obstacle())
		self.field.set_cell(door_pos.x, door_pos.y, self.door())

class BSPBuildingBuilder(object):
	""" Fills specified field with buildings set in binary space partition.
	Uses tuples generated by BinarySpacePartition.
	"""
	def __init__(self, field, free=False, obstacle=True, door=False):
		self.field = field
		self.free, self.obstacle, self.door = free, obstacle, door
	def fill(self, topleft, bottomright, is_horizontal, door_pos):
		for x in range(topleft.x + 3, bottomright.x + 1 - 3):
			for y in range(topleft.y + 3, bottomright.y + 1 - 3):
				self.field.set_cell(x, y, self.obstacle())
		if is_horizontal:
			the_divide = door_pos.x
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell(the_divide - 1, y, self.free())
				self.field.set_cell(the_divide, y, self.free())
				self.field.set_cell(the_divide + 1, y, self.free())
		else:
			the_divide = door_pos.y
			for x in range(topleft.x, bottomright.x + 1):
				self.field.set_cell(x, the_divide - 1, self.free())
				self.field.set_cell(x, the_divide, self.free())
				self.field.set_cell(x, the_divide + 1, self.free())
		self.field.set_cell(door_pos.x, door_pos.y, self.door())

class BSPDungeon(Builder):
	def _build(self):
		Log.debug("Building surrounding walls.")
		for x in range(self.size.width):
			self.strata.set_cell(x, 0, 'wall')
			self.strata.set_cell(x, self.size.height - 1, 'wall')
		for y in range(self.size.height):
			self.strata.set_cell(0, y, 'wall')
			self.strata.set_cell(self.size.width - 1, y, 'wall')

		Log.debug("Running BSP...")
		bsp = BinarySpacePartition(self.rng)
		builder = BSPBuilder(self.strata,
								 free=lambda: 'floor',
								 obstacle=lambda: 'wall',
								 door=lambda: 'floor',
						 )
		for splitter in bsp.generate(Point(1, 1), Point(self.size.width - 2, self.size.height - 2)):
			Log.debug("Splitter: {0}".format(splitter))
			builder.fill(*splitter)

		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) == 'floor'
		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		Log.debug("Generated player pos: {0}".format(self.start_pos))

		self.exit_pos = pcg.pos(self.rng, self.size, lambda pos: floor_only(pos) and pos != self.start_pos)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

class CityBuilder(Builder):
	def _build(self):
		Log.debug("Building surrounding walls.")
		for x in range(self.size.width):
			self.strata.set_cell(x, 0, 'wall')
			self.strata.set_cell(x, self.size.height - 1, 'wall')
		for y in range(self.size.height):
			self.strata.set_cell(0, y, 'wall')
			self.strata.set_cell(self.size.width - 1, y, 'wall')
		for x in range(1, self.size.width - 1):
			for y in range(1, self.size.height - 1):
				self.strata.set_cell(x, y, 'floor')

		Log.debug("Running BSP...")
		bsp = BinarySpacePartition(self.rng, min_width=8, min_height=7)
		bsp.set_unfit_both_dimensions(True)
		builder = BSPBuildingBuilder(self.strata,
								 free=lambda: 'floor',
								 obstacle=lambda: 'wall',
								 door=lambda: 'floor',
						 )
		for splitter in bsp.generate(Point(1, 1), Point(self.size.width - 2, self.size.height - 2)):
			Log.debug("Splitter: {0}".format(splitter))
			builder.fill(*splitter)

		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) == 'floor'
		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		Log.debug("Generated player pos: {0}".format(self.start_pos))

		self.exit_pos = pcg.pos(self.rng, self.size, lambda pos: floor_only(pos) and pos != self.start_pos)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

class CaveBuilder(Builder):
	NEIGHS = [
			(-1, -1), (-1, 0), (-1, 1),
			( 0, -1),          ( 0, 1),
			(+1, -1), (+1, 0), (+1, 1),
			]
	NEIGHS_2 = [
			(-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
			(-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2),
			( 0, -2), ( 0, -1), ( 0, 0),  ( 0, 1), ( 0, 2),
			(+1, -2), (+1, -1), (+1, 0), (+1, 1), (+1, 2),
			(+2, -2), (+2, -1), (+2, 0), (+2, 1), (+2, 2),
			]
	def _build(self):
		self.strata = Matrix(self.size, 0)
		for x in range(1, self.strata.size.width - 1):
			for y in range(1, self.strata.size.height - 1):
				self.strata.set_cell(x, y, 0 if self.rng.get() < 0.50 else 1)
		Log.debug("Initial state:\n{0}".format(repr(self.strata)))

		new_layer = Matrix(self.strata.size)
		drop_wall_2_at = 4
		for step in range(drop_wall_2_at+1):
			for x in range(1, self.strata.size.width - 1):
				for y in range(1, self.strata.size.height - 1):
					wall_count = 0
					for n in self.NEIGHS:
						if self.strata.cell(x + n[0], y + n[1]) == 0:
							wall_count += 1
							if wall_count >= 5:
								break
					if wall_count >= 5:
						new_layer.set_cell(x, y, 0)
						continue
					if step < drop_wall_2_at:
						wall_2_count = 0
						for n in self.NEIGHS_2:
							n = Point(x + n[0], y + n[1])
							if not self.strata.valid(n):
								continue
							if self.strata.cell(n.x, n.y) == 0:
								wall_2_count += 1
								if wall_2_count > 2:
									break
						if wall_2_count <= 2:
							new_layer.set_cell(x, y, 0)
							continue
					new_layer.set_cell(x, y, 1)
			self.strata, new_layer = new_layer, self.strata
			Log.debug("Step {1}:\n{0}".format(repr(self.strata), step))
		
		cavern = next(pos for pos in self.strata.size if self.strata.cell(pos.x, pos.y) == 1)
		caverns = []
		while cavern:
			area = []
			already_affected = {cavern}
			last_wave = {cavern}
			area.append(cavern)
			while last_wave:
				Log.debug('Last wave: {0}'.format(len(last_wave)))
				wave = set()
				for point in last_wave:
					wave |= {x for x in self.strata.get_neighbours(point.x, point.y) if self.strata.cell(x.x, x.y) == 1}
				for point in wave - already_affected:
					area.append(point)
				last_wave = wave - already_affected
				already_affected |= wave

			count = 0
			for point in area:
				count += 1
				self.strata.set_cell(point.x, point.y, 2 + len(caverns))
			caverns.append(count)
			Log.debug("Filling cavern #{1}:\n{0}".format(repr(self.strata), len(caverns)))
			cavern = next((pos for pos in self.strata.size if self.strata.cell(pos.x, pos.y) == 1), None)
		max_cavern = 2 + caverns.index(max(caverns))
		for pos in self.strata.size:
			if self.strata.cell(pos.x, pos.y) in [0, max_cavern]:
				continue
			self.strata.set_cell(pos.x, pos.y, 0)
		Log.debug("Finalized cave:\n{0}".format(repr(self.strata)))

		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) > 1
		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		self.exit_pos = pcg.pos(self.rng, self.size, lambda pos: floor_only(pos) and pos != self.start_pos)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

		for pos in self.strata.size:
			if self.strata.cell(pos.x, pos.y):
				self.strata.set_cell(pos.x, pos.y, 'floor')
			else:
				self.strata.set_cell(pos.x, pos.y, 'wall')

# this changes the direction to go from the current square, to the next available
def RandomDirections(rng):
	direction = rng.range(4)
	if direction == 0:
		cDir = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)]
	elif direction == 1:
		cDir = [Point(0, 1), Point(0, -1), Point(1, 0), Point(-1, 0)]
	elif direction == 2:
		cDir = [Point(0, -1), Point(0, 1), Point(-1, 0), Point(1, 0)]
	elif direction == 3:
		cDir = [Point(1, 0), Point(-1, 0), Point(0, 1), Point(0, -1)]
	return cDir

class MazeBuilder(Builder):
	CELL_SIZE = Size(1, 1)
	def _make_maze(self):
		layout_size = Size(
				# Layout size should be odd (for connections between cells).
				(self.size.width - 2 - (1 - self.size.width % 2)) // self.CELL_SIZE.width,
				(self.size.height - 2 - (1 - self.size.height % 2)) // self.CELL_SIZE.height,
				) # For walls.
		layout = Matrix(layout_size, False)

		# 0 is the most random, randomisation gets lower after that
		# less randomisation means more straight corridors
		RANDOMISATION = 0

		intDone = 0
		while intDone + 1 < ((layout_size.width + 1) * (layout_size.height + 1)) / 4:
			expected = ((layout_size.width + 1) * (layout_size.height + 1)) / 4
			# Search only for cells that have potential option to expand.
			potential_exits = 0
			while not potential_exits:
				# this code is used to make sure the numbers are odd
				current = Point(
					self.rng.range(((layout_size.width + 1) // 2)) * 2,
					self.rng.range(((layout_size.height + 1) // 2)) * 2,
					)
				Log.debug((current, layout_size))
				if current.x > 1 and not layout.cell(current.x - 2, current.y):
					potential_exits += 1
				if current.y > 1 and not layout.cell(current.x, current.y - 2):
					potential_exits += 1
				if current.x <= layout_size.width - 2 and not layout.cell(current.x + 2, current.y):
					potential_exits += 1
				if current.y <= layout_size.height - 2 and not layout.cell(current.x, current.y + 2):
					potential_exits += 1
			# first one is free!
			if intDone == 0:
				layout.set_cell(current.x, current.y, True)
			if not layout.cell(current.x, current.y):
				continue
			layout.set_cell(current.x, current.y, 123)
			layout.set_cell(current.x, current.y, True)
			# always randomisation directions to start
			cDir = RandomDirections(self.rng)
			blnBlocked = False
			while not blnBlocked:
				# only randomisation directions, based on the constant
				if RANDOMISATION == 0 or self.rng.range(RANDOMISATION) == 0:
					cDir = RandomDirections(self.rng)
				blnBlocked = True
				# loop through order of directions
				for intDir in range(4):
					# work out where this direction is
					new_cell = Point(
							current.x + (cDir[intDir].x * 2),
							current.y + (cDir[intDir].y * 2),
							)
					# check if the tile can be used
					if not layout.valid(new_cell) or layout.cell(new_cell.x, new_cell.y):
						continue
					# create a path
					layout.set_cell(new_cell.x, new_cell.y, True)
					# and the square inbetween
					layout.set_cell(current.x + cDir[intDir].x, current.y + cDir[intDir].y, True)
					# this is now the current square
					current = new_cell
					blnBlocked = False
					# increment paths created
					intDone = intDone + 1
					break
		Log.debug("Done {0}/{1} cells:\n{2}".format(intDone, expected, layout.tostring(lambda c:'#' if c else '.')))
		return layout
	def _fill_maze(self, layout):
		self.strata = Matrix(self.size, 'wall')
		for pos in layout.size:
			if layout.cell(pos.x, pos.y):
				for x in range(self.CELL_SIZE.width):
					for y in range(self.CELL_SIZE.height):
						self.strata.set_cell(
								1 + pos.x * self.CELL_SIZE.width + x,
								1 + pos.y * self.CELL_SIZE.height + y,
								'floor',
								)
	def _place_points(self):
		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) == 'floor'
		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		Log.debug("Generated player pos: {0}".format(self.start_pos))

		self.exit_pos = pcg.pos(self.rng, self.size, lambda pos: floor_only(pos) and pos != self.start_pos)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))
	def _build(self):
		layout = self._make_maze()
		self._fill_maze(layout)
		self._place_points()

class Sewers(MazeBuilder):
	CELL_SIZE = Size(4, 3)
	def _fill_maze(self, layout):
		super(Sewers, self)._fill_maze(layout)

		# Fill water streams.
		for x in range(self.size.width):
			for y in range(self.size.height):
				if self.strata.cell(x, y) == 'wall':
					continue
				for n in self.strata.get_neighbours(x, y, with_diagonal=True):
					if self.strata.cell(n.x, n.y) == 'wall':
						break
				else:
					self.strata.set_cell(x, y, 'water')
