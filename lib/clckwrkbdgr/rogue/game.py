import os
import copy
import random
import itertools
from collections import namedtuple
import curses
from .math import Point, Matrix, Size, Rect
from .messages import Log

SAVEFILE_VERSION = 1

class Cell: # pragma: no cover -- TODO
	def __init__(self, sprite, passable=True, remembered=None):
		self.sprite = sprite
		self.passable = passable
		self.remembered = remembered
		self.visited = False
	def __str__(self):
		return '*' if self.visited else '.'

def bresenham(start, stop): # pragma: no cover -- TODO
	dx = abs(stop.x - start.x)
	sx = 1 if start.x < stop.x else -1
	dy = -abs(stop.y - start.y)
	sy = 1 if start.y < stop.y else -1
	error = dx + dy
	
	x, y = start.x, start.y
	while True:
		yield Point(x, y)
		if x == stop.x and y == stop.y:
			break
		e2 = 2 * error
		if e2 >= dy:
			if x == stop.x:
				break
			error = error + dy
			x += sx
		if e2 <= dx:
			if y == stop.y:
				break
			error = error + dx
			y += sy

def build_rogue_dungeon(size): # pragma: no cover -- TODO
	strata = Matrix(size, Cell(' ', False))

	map_size = strata.size
	grid_size = Size(3, 3)
	min_room_size = Size(4, 4)
	margin = Size(1, 1)
	grid = Matrix(grid_size)
	cell_size = Size(map_size.width // grid_size.width, map_size.height // grid_size.height)
	max_room_size = Size(
			cell_size.width - margin.width * 2,
			cell_size.height - margin.height * 2
			)
	if max_room_size.width < min_room_size.width:
		max_room_size.width = min_room_size.width
	if max_room_size.height < min_room_size.height:
		max_room_size.height = min_room_size.height
	for cell in grid.size:
		room_size = Size(
				random.randrange(min_room_size.width, max_room_size.width + 1),
				random.randrange(min_room_size.height, max_room_size.height + 1),
				)
		topleft = Point(cell.x * cell_size.width, cell.y * cell_size.height)
		random_non_negative = lambda _:random.randrange(_) if _ > 0 else 0
		topleft += Point(
				random_non_negative(cell_size.width - room_size.width - 1),
				random_non_negative(cell_size.height - room_size.height - 1),
				)
		grid.set_cell(cell.x, cell.y, Rect(topleft, room_size))

	maze = {k:set() for k in grid.keys()}
	for column in range(grid.width):
		for row in range(grid.height):
			if column < grid.width - 1:
				a, b = Point(column, row), Point(column + 1, row)
				maze[a].add(b)
				maze[b].add(a)
			if row < grid.height - 1:
				a, b = Point(column, row), Point(column, row + 1)
				maze[a].add(b)
				maze[b].add(a)
	for i in range(5):
		new_config = copy.deepcopy(maze)
		all_links = set(tuple(sorted((node_from, node_to))) for node_from in maze for node_to in maze[node_from])
		removed = random.choice(list(all_links))
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
	for start_room, stop_room in all_links:
		assert abs(start_room.x - stop_room.x) + abs(start_room.y - stop_room.y) == 1
		if abs(start_room.x - stop_room.x) > 0:
			direction = 'H'
		else:
			direction = 'V'
		start_room = grid.cell(start_room.x, start_room.y)
		stop_room = grid.cell(stop_room.x, stop_room.y)

		bending_point = 1
		if direction == 'H':
			if start_room.topleft.x > stop_room.topleft.x:
				start_room, stop_room = stop_room, start_room
			start = Point(
				start_room.topleft.x + start_room.size.width,
				random.randrange(start_room.topleft.y+1, start_room.topleft.y + stop_room.size.height),
				)
			stop = Point(
				stop_room.topleft.x,
				random.randrange(stop_room.topleft.y+1, stop_room.topleft.y + stop_room.size.height),
				)
			if abs(stop_room.topleft.x - (start_room.topleft.x + start_room.size.width)) > 1:
				bending_point = random.randrange(1, abs(stop_room.topleft.x - (start_room.topleft.x + start_room.size.width)))
		else:
			if start_room.topleft.y > stop_room.topleft.y:
				start_room, stop_room = stop_room, start_room
			start = Point(
				random.randrange(start_room.topleft.x+1, start_room.topleft.x+start_room.size.width),
				start_room.topleft.y + start_room.size.height,
				)
			stop = Point(
				random.randrange(stop_room.topleft.x+1, stop_room.topleft.x+stop_room.size.width),
				stop_room.topleft.y,
				)
			if abs(stop_room.topleft.y - (start_room.topleft.y + start_room.size.height)) > 1:
				bending_point = random.randrange(1, abs(stop_room.topleft.y - (start_room.topleft.y + start_room.size.height)))
		tunnels.append((
			start,
			stop,
			direction,
			bending_point,
			))

	for room in grid.size:
		room = grid.cell(room.x, room.y)
		strata.set_cell(room.topleft.x, room.topleft.y, Cell("+", False, remembered='+'))
		strata.set_cell(room.topleft.x, room.topleft.y+room.size.height, Cell("+", False, remembered='+'))
		strata.set_cell(room.topleft.x+room.size.width, room.topleft.y, Cell("+", False, remembered='+'))
		strata.set_cell(room.topleft.x+room.size.width, room.topleft.y+room.size.height, Cell("+", False, remembered='+'))
		for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
			strata.set_cell(x, room.topleft.y, Cell("-", False, remembered='-'))
			strata.set_cell(x, room.topleft.y+room.size.height, Cell("-", False, remembered='-'))
		for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
			strata.set_cell(room.topleft.x, y, Cell("|", False, remembered='|'))
			strata.set_cell(room.topleft.x+room.size.width, y, Cell("|", False, remembered='|'))
		for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
			for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
				strata.set_cell(x, y, Cell(".", True))

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
			strata.set_cell(cell.x, cell.y, Cell("#", True, remembered='#'))
		strata.set_cell(start.x, start.y, Cell("+", True, remembered='+'))
		strata.set_cell(stop.x, stop.y, Cell("+", True, remembered='+'))

	enter_room_key = random.choice(list(grid.keys()))
	enter_room = grid.cell(enter_room_key.x, enter_room_key.y)
	start_pos = Point(
				random.randrange(enter_room.topleft.x + 1, enter_room.topleft.x + enter_room.size.width + 1 - 1),
				random.randrange(enter_room.topleft.y + 1, enter_room.topleft.y + enter_room.size.height + 1 - 1),
				)

	for _ in range(9):
		exit_room_key = random.choice(list(grid.keys()))
		exit_room = grid.cell(exit_room_key.x, exit_room_key.y)
		exit_pos = Point(
				random.randrange(exit_room.topleft.x + 1, exit_room.topleft.x + exit_room.size.width + 1 - 1),
				random.randrange(exit_room.topleft.y + 1, exit_room.topleft.y + exit_room.size.height + 1 - 1),
				)
		if exit_room_key != enter_room_key:
			break
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	return start_pos, exit_pos, strata

def generate_single_pos(size): # pragma: no cover -- TODO
	return Point(random.randrange(size.width), random.randrange(size.height))

def generate_pos(size, check=None, counter=1000): # pragma: no cover -- TODO
	result = generate_single_pos(size)
	while counter > 0 and not check(result):
		result = generate_single_pos(size)
		counter -= 1
	return result

class BinarySpacePartition(object): # pragma: no cover -- TODO
	def __init__(self, min_width=15, min_height=10):
		self.min_size = (min_width, min_height)
	def door_generator(self, room): # pragma: no cover
		""" Takes a Rect object and generates random Point for door position inside it.
		No need to determine wall facing and location, the algorithm would decide automatically.
		By default door is generated in random manner.
		"""
		x = random.randrange(room.topleft.x, room.topleft.x + room.size.width - 1)
		y = random.randrange(room.topleft.y, room.topleft.y + room.size.height - 1)
		Log.debug("Generating door in {0}:  ({1}, {2})".format(room, x, y))
		return Point(x, y)
	def hor_ver_generator(self): # pragma: no cover
		""" Used to determine direction of the split for the current room.
		It should return True for horizontal and False for vertical room.
		By default these values are generated in random manner.
		"""
		return random.choice([False, True])
	def generate(self, topleft, bottomright):
		""" Generates BS partition for given rectangle.
		Yield tuples (topleft, bottomright, is_horizontal, door).
		Tuples go from the biggest room to the all subrooms descending.
		Sibling rooms go left-to-right and top-to-bottom.
		"""
		Log.debug("topleft={0}, bottomright={1}".format(topleft, bottomright))
		too_narrow = abs(topleft.x - bottomright.x) <= self.min_size[0]
		too_low = abs(topleft.y - bottomright.y) <= self.min_size[1]
		if too_narrow and too_low:
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
		if userspace.size.width <= 1 or userspace.size.height <= 1: # TODO why is it needed?
			return
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

class BSPBuilder(object): # pragma: no cover -- TODO
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

def build_bsp_dungeon(size): # pragma: no cover -- TODO
	strata = Matrix(size, Cell(' ', False))

	Log.debug("Building surrounding walls.")
	for x in range(size.width):
		strata.set_cell(x, 0, Cell('#', False, remembered='#'))
		strata.set_cell(x, size.height - 1, Cell('#', False, remembered='#'))
	for y in range(size.height):
		strata.set_cell(0, y, Cell('#', False, remembered='#'))
		strata.set_cell(size.width - 1, y, Cell('#', False, remembered='#'))

	Log.debug("Running BSP...")
	bsp = BinarySpacePartition()
	builder = BSPBuilder(strata,
							 free=lambda: Cell('.'),
							 obstacle=lambda: Cell('#', False, remembered='#'),
							 door=lambda: Cell('.'),
					 )
	for splitter in bsp.generate(Point(1, 1), Point(size.width - 2, size.height - 2)):
		Log.debug("Splitter: {0}".format(splitter))
		builder.fill(*splitter)

	floor_only = lambda pos: strata.cell(pos.x, pos.y).passable
	start_pos = generate_pos(size, floor_only)
	Log.debug("Generated player pos: {0}".format(start_pos))

	exit_pos = generate_pos(size, lambda pos: floor_only(pos) and pos != start_pos)
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	return start_pos, exit_pos, strata

def build_cave(size): # pragma: no cover -- TODO
	strata = Matrix(size, 0)
	for x in range(1, strata.width - 1):
		for y in range(1, strata.height - 1):
			strata.set_cell(x, y, 0 if random.random() < 0.50 else 1)
	Log.debug("Initial state:\n{0}".format(repr(strata)))

	new_layer = Matrix(strata.size)
	drop_wall_2_at = 4
	for step in range(drop_wall_2_at+1):
		for x in range(1, strata.width - 1):
			for y in range(1, strata.height - 1):
				neighs = set(strata.get_neighbours(x, y, with_diagonal=True))
				neighs2 = set(itertools.chain.from_iterable(
					strata.get_neighbours(n.x, n.y, with_diagonal=True)
					for n in neighs
					)) - set(Point(x, y))
				wall_count = sum(int(strata.cell(n.x, n.y) == 0) for n in neighs)
				wall_2_count = sum(int(strata.cell(n.x, n.y) == 0) for n in neighs2)
				is_wall = strata.cell(x, y) == 0
				if wall_count >= 5:
					new_layer.set_cell(x, y, 0)
				elif step < drop_wall_2_at and wall_2_count <= 2:
					new_layer.set_cell(x, y, 0)
				else:
					new_layer.set_cell(x, y, 1)
		strata, new_layer = new_layer, strata
		Log.debug("Step {1}:\n{0}".format(repr(strata), step))
	
	cavern = next(pos for pos in strata.size if strata.cell(pos.x, pos.y) == 1)
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
				wave |= {x for x in strata.get_neighbours(point.x, point.y) if strata.cell(x.x, x.y) == 1}
			for point in wave - already_affected:
				area.append(point)
			last_wave = wave - already_affected
			already_affected |= wave

		count = 0
		for point in area:
			count += 1
			strata.set_cell(point.x, point.y, 2 + len(caverns))
		caverns.append(count)
		Log.debug("Filling cavern #{1}:\n{0}".format(repr(strata), len(caverns)))
		cavern = next((pos for pos in strata.size if strata.cell(pos.x, pos.y) == 1), None)
	max_cavern = 2 + caverns.index(max(caverns))
	for pos in strata.size:
		if strata.cell(pos.x, pos.y) in [0, max_cavern]:
			continue
		strata.set_cell(pos.x, pos.y, 0)
	Log.debug("Finalized cave:\n{0}".format(repr(strata)))

	floor_only = lambda pos: strata.cell(pos.x, pos.y) > 1
	start_pos = generate_pos(size, floor_only)
	exit_pos = generate_pos(size, lambda pos: floor_only(pos) and pos != start_pos)
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	for pos in strata.size:
		if strata.cell(pos.x, pos.y):
			strata.set_cell(pos.x, pos.y, Cell('.'))
		else:
			strata.set_cell(pos.x, pos.y, Cell('#', False, remembered='#'))

	return start_pos, exit_pos, strata

# this changes the direction to go from the current square, to the next available
def RandomDirections(): # pragma: no cover -- TODO
	direction = random.randrange(4)
	if direction == 0:
		cDir = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)]
	elif direction == 1:
		cDir = [Point(0, 1), Point(0, -1), Point(1, 0), Point(-1, 0)]
	elif direction == 2:
		cDir = [Point(0, -1), Point(0, 1), Point(-1, 0), Point(1, 0)]
	elif direction == 3:
		cDir = [Point(1, 0), Point(-1, 0), Point(0, 1), Point(0, -1)]
	return cDir

def build_maze(size): # pragma: no cover -- TODO
	layout_size = Size(
			# Layout size should be odd (for connections between cells).
			size.width - 2 - (1 - size.width % 2),
			size.height - 2 - (1 - size.height % 2),
			) # For walls.
	layout = Matrix(layout_size, False)

	# 0 is the most random, randomisation gets lower after that
	# less randomisation means more straight corridors
	RANDOMISATION = 0

	intDone = 0
	while True:
		expected = ((layout_size.width + 1) * (layout_size.height + 1)) / 4
		Log.debug("Done {0}/{1} cells:\n{2}".format(intDone, expected, repr(layout)))
		# this code is used to make sure the numbers are odd
		current = Point(
				random.randrange((layout_size.width // 2)) * 2,
				random.randrange((layout_size.height // 2)) * 2,
				)
		# first one is free!
		if intDone == 0:
			layout.set_cell(current.x, current.y, True)
		if layout.cell(current.x, current.y):
			# always randomisation directions to start
			cDir = RandomDirections()
			blnBlocked = False
			while not blnBlocked:
				# only randomisation directions, based on the constant
				if RANDOMISATION == 0 or random.randrange(RANDOMISATION) == 0:
					cDir = RandomDirections()
				blnBlocked = True
				# loop through order of directions
				for intDir in range(4):
					# work out where this direction is
					new_cell = Point(
							current.x + (cDir[intDir].x * 2),
							current.y + (cDir[intDir].y * 2),
							)
					# check if the tile can be used
					if layout.valid(new_cell) and not layout.cell(new_cell.x, new_cell.y):
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
		if not ( intDone + 1 < ((layout_size.width + 1) * (layout_size.height + 1)) / 4):
			break

	strata = Matrix(size, Cell('#', False, remembered='#')) # FIXME
	for pos in layout.size:
		if layout.cell(pos.x, pos.y):
			strata.set_cell(pos.x + 1, pos.y + 1, Cell('.'))

	floor_only = lambda pos: strata.cell(pos.x, pos.y).passable
	start_pos = generate_pos(size, floor_only)
	Log.debug("Generated player pos: {0}".format(start_pos))

	exit_pos = generate_pos(size, lambda pos: floor_only(pos) and pos != start_pos)
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	return start_pos, exit_pos, strata

class Game: # pragma: no cover -- TODO
	def __init__(self, start_pos, exit_pos, strata):
		self.player = start_pos
		self.exit_pos = exit_pos
		self.remembered_exit = False
		self.strata = strata

def save_game(game): # pragma: no cover -- TODO
	dump_str = lambda _value: _value if _value is None else _value
	dump_bool = lambda _value: int(_value)
	yield game.player.x
	yield game.player.y
	yield game.exit_pos.x
	yield game.exit_pos.y
	yield dump_bool(game.remembered_exit)
	yield game.strata.size.width
	yield game.strata.size.height
	for cell in game.strata.cells:
		yield cell.sprite
		yield dump_bool(cell.passable)
		yield cell.remembered
		yield dump_bool(cell.visited)

def load_game(version, data): # pragma: no cover -- TODO
	parse_str = lambda _value: _value if _value != 'None' else None
	parse_bool = lambda _value: _value == '1'

	player = Point(int(next(data)), int(next(data)))
	exit_pos = Point(int(next(data)), int(next(data)))
	remembered_exit = parse_bool(next(data))

	strata_size = Size(int(next(data)), int(next(data)))
	strata = Matrix(strata_size, None)
	for _ in range(strata_size.width * strata_size.height):
		strata.cells[_] = Cell(
				parse_str(next(data)),
				parse_bool(next(data)),
				parse_str(next(data)),
				)
		strata.cells[_].visited = parse_bool(next(data))

	game = Game(player, exit_pos, strata)
	game.remembered_exit = remembered_exit
	return game

def main_loop(window): # pragma: no cover -- TODO
	curses.curs_set(0)
	builders = [
			build_bsp_dungeon,
			build_rogue_dungeon,
			build_cave,
			build_maze,
			]
	savefile = os.path.expanduser('~/.rogue.sav')
	if os.path.exists(savefile):
		Log.debug('Loading savefile: {0}...'.format(savefile))
		with open(savefile, 'r') as f:
			data = f.read().split('\0')
		data = iter(data)
		version = next(data)
		game = load_game(version, data)
		Log.debug('Loaded.')
		Log.debug(repr(game.strata))
		Log.debug('Player: {0}'.format(game.player))
	else:
		builder = random.choice(builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		player, exit_pos, strata = builder(Size(80, 23))
		game = Game(player, exit_pos, strata)
	field_of_view = Matrix(Size(21, 21), False)
	playing = True
	god_vision = False
	Log.debug('Starting playing...')
	alive = True
	while playing:
		Log.debug('Recalculating Field Of View.')
		field_of_view.clear(False)
		for pos in field_of_view.size:
			Log.debug('FOV pos: {0}'.format(pos))
			half_size = Size(field_of_view.size.width // 2, field_of_view.size.height // 2)
			rel_pos = Point(
					half_size.width - pos.x,
					half_size.height - pos.y,
					)
			Log.debug('FOV rel pos: {0}'.format(rel_pos))
			if (rel_pos.x / half_size.width) ** 2 + (rel_pos.y / half_size.height) ** 2 <= 1:
				Log.debug('Is inside FOV ellipse.')
				Log.debug('Traversing line of sight: [0;0] -> {0}'.format(rel_pos))
				for inner_line_pos in bresenham(Point(0, 0), rel_pos):
					real_world_pos = game.player + inner_line_pos
					Log.debug('Line pos: {0}, real world pos: {1}'.format(inner_line_pos, real_world_pos))
					fov_pos = Point(half_size.width + inner_line_pos.x,
							half_size.height + inner_line_pos.y,
							)
					if not game.strata.valid(real_world_pos):
						continue
					Log.debug('Setting as visible: {0}'.format(fov_pos))
					cell = game.strata.cell(real_world_pos.x, real_world_pos.y)
					cell.visited = True
					field_of_view.set_cell(fov_pos.x, fov_pos.y, True)
					if not cell.passable:
						Log.debug('Not passable, stop: {0}'.format(repr(cell.sprite)))
						break
		Log.debug("Full FOV:\n{0}".format(repr(field_of_view)))

		Log.debug('Redrawing interface.')
		Log.debug('Player at: {0}'.format(game.player))
		for row in range(game.strata.height):
			for col in range(game.strata.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				cell = game.strata.cell(col, row)
				rel_pos = Point(col, row) - game.player
				Log.debug('Relative pos: {0}'.format(rel_pos))

				is_visible = False
				fov_pos = rel_pos + Point(
						field_of_view.size.width // 2,
						field_of_view.size.height // 2,
						)
				Log.debug('Relative FOV pos: {0}'.format(fov_pos))
				if field_of_view.valid(fov_pos):
					is_visible = field_of_view.cell(fov_pos.x, fov_pos.y)
					Log.debug('Valid FOV pos, is visible: {0}'.format(is_visible))
				Log.debug('Visible: {0}'.format(is_visible))

				if is_visible or god_vision:
					window.addstr(1+row, col, cell.sprite)
				elif cell.visited and cell.remembered:
					window.addstr(1+row, col, cell.remembered)
				else:
					window.addstr(1+row, col, ' ')

		is_exit_visible = False
		exit_rel_pos = game.exit_pos - game.player
		exit_fov_pos = exit_rel_pos + Point(
				field_of_view.size.width // 2,
				field_of_view.size.height // 2,
				)
		if field_of_view.valid(exit_fov_pos):
			is_exit_visible = field_of_view.cell(exit_fov_pos.x, exit_fov_pos.y)
			if is_exit_visible:
				game.remembered_exit = True
		if is_exit_visible or god_vision or game.remembered_exit:
			window.addstr(1+game.exit_pos.y, game.exit_pos.x, '>')

		window.addstr(1+game.player.y, game.player.x, '@')

		status = []
		if god_vision:
			status.append('[vis]')
		window.addstr(24, 0, (' '.join(status) + " " * 80)[:80])
		window.refresh()

		Log.debug('Performing user actions.')
		control = window.getch()
		Log.debug('Control: {0} ({1}).'.format(control, repr(chr(control))))
		if control == ord('q'):
			Log.debug('Exiting the game.')
			playing = False
			break
		elif control == ord('v'):
			god_vision = not god_vision
		elif control == ord('Q'):
			Log.debug('Suicide.')
			alive = False
			playing = False
			break
		elif control == ord('>'):
			if game.player == game.exit_pos:
				builder = random.choice(builders)
				Log.debug('Building new dungeon: {0}...'.format(builder))
				player, exit_pos, strata = builder(Size(80, 23))
				game = Game(player, exit_pos, strata)
		elif chr(control) in 'hjklyubn':
			Log.debug('Moving.')
			shift = {
					'h' : Point(-1,  0),
					'j' : Point( 0, +1),
					'k' : Point( 0, -1),
					'l' : Point(+1,  0),
					'y' : Point(-1, -1),
					'u' : Point(+1, -1),
					'b' : Point(-1, +1),
					'n' : Point(+1, +1),
					}[chr(control)]
			Log.debug('Shift: {0}'.format(shift))
			new_pos = game.player + shift
			if game.strata.valid(new_pos) and game.strata.cell(new_pos.x, new_pos.y).passable:
				Log.debug('Shift is valid, updating player pos: {0}'.format(game.player))
				game.player = new_pos
	if alive:
		dump = save_game(game)
		with open(savefile, 'w') as f:
			f.write(str(SAVEFILE_VERSION) + '\0')
			f.write('\0'.join(map(str, dump)))
	elif os.path.exists(savefile):
		os.unlink(savefile)

def run(): # pragma: no cover
	curses.wrapper(main_loop)
