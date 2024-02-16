import sys
import copy
import random
import itertools
from collections import namedtuple
import logging
Log = logging.getLogger('rogue')
import curses
import jsonpickle
from clckwrkbdgr import xdg
from clckwrkbdgr.math import Point, Matrix, Size, Rect
import clckwrkbdgr.math.graph, clckwrkbdgr.math.algorithm
import clckwrkbdgr.logging

class Cell:
	def __init__(self, sprite, passable=True):
		self.sprite = sprite
		self.passable = passable

def bresenham(start, stop):
	dx = abs(stop.x - start.x)
	sx = 1 if start.x < stop.x else -1
	dy = -abs(stop.y - start.y)
	sy = 1 if start.y < stop.y else -1
	error = dx + dy
	
	while True:
		yield start
		if start.x == stop.x and start.y == stop.y:
			break
		e2 = 2 * error
		if e2 >= dy:
			if start.x == stop.x:
				break
			error = error + dy
			start.x += sx
		if e2 <= dx:
			if start.y == stop.y:
				break
			error = error + dx
			start.y += sy

def build_rogue_dungeon(size):
	strata = Matrix(size, Cell(' ', False))

	map_size = strata.size
	grid_size = Size(3, 3)
	min_room_size = Size(4, 4)
	margin = Size(1, 1)
	grid = Matrix(grid_size)
	cell_size = Size(map_size.width // grid_size.width, map_size.height // grid_size.height)
	max_room_size = cell_size - margin * 2
	if max_room_size.width < min_room_size.width:
		max_room_size.width = min_room_size.width
	if max_room_size.height < min_room_size.height:
		max_room_size.height = min_room_size.height
	for cell in grid:
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
		grid.set_cell(cell, Rect(topleft, room_size))

	maze = clckwrkbdgr.math.graph.grid_from_matrix(grid)
	for i in range(5):
		new_config = copy.copy(maze)
		removed = random.choice(list(maze.all_links()))
		new_config.disconnect(*removed)
		if clckwrkbdgr.math.graph.is_connected(new_config):
			maze = new_config

	tunnels = []
	for start_room, stop_room in maze.all_links():
		assert abs(start_room.x - stop_room.x) + abs(start_room.y - stop_room.y) == 1
		if abs(start_room.x - stop_room.x) > 0:
			direction = 'H'
		else:
			direction = 'V'
		start_room = grid.cell(start_room)
		stop_room = grid.cell(stop_room)

		bending_point = 1
		if direction == 'H':
			if start_room.left > stop_room.left:
				start_room, stop_room = stop_room, start_room
			start = Point(
				start_room.right,
				random.randrange(start_room.top+1, start_room.bottom),
				)
			stop = Point(
				stop_room.left,
				random.randrange(stop_room.top+1, stop_room.bottom),
				)
			if abs(stop_room.left - start_room.right) > 1:
				bending_point = random.randrange(1, abs(stop_room.left - start_room.right))
		else:
			if start_room.top > stop_room.top:
				start_room, stop_room = stop_room, start_room
			start = Point(
				random.randrange(start_room.left+1, start_room.right),
				start_room.bottom,
				)
			stop = Point(
				random.randrange(stop_room.left+1, stop_room.right),
				stop_room.top,
				)
			if abs(stop_room.top - start_room.bottom) > 1:
				bending_point = random.randrange(1, abs(stop_room.top - start_room.bottom))
		tunnels.append(clckwrkbdgr.math.geometry.RectConnection(
			start=start,
			stop=stop,
			direction=direction,
			bending_point=bending_point,
			))

	for room in grid.values():
		strata.set_cell((room.left, room.top), Cell("+", False))
		strata.set_cell((room.left, room.bottom), Cell("+", False))
		strata.set_cell((room.right, room.top), Cell("+", False))
		strata.set_cell((room.right, room.bottom), Cell("+", False))
		for x in range(room.left+1, room.right):
			strata.set_cell((x, room.top), Cell("-", False))
			strata.set_cell((x, room.bottom), Cell("-", False))
		for y in range(room.top+1, room.bottom):
			strata.set_cell((room.left, y), Cell("|", False))
			strata.set_cell((room.right, y), Cell("|", False))
		for y in range(room.top+1, room.bottom):
			for x in range(room.left+1, room.right):
				strata.set_cell((x, y), Cell(".", True))

	for tunnel in tunnels:
		for cell in tunnel.iter_points():
			strata.set_cell((cell.x, cell.y), Cell("#", True))
		strata.set_cell((tunnel.start.x, tunnel.start.y), Cell("+", True))
		strata.set_cell((tunnel.stop.x, tunnel.stop.y), Cell("+", True))

	enter_room_key = random.choice(list(grid.keys()))
	enter_room = grid.cell(enter_room_key)
	start_pos = Point(
				random.randrange(enter_room.left + 1, enter_room.right + 1 - 1),
				random.randrange(enter_room.top + 1, enter_room.bottom + 1 - 1),
				)

	for _ in range(9):
		exit_room_key = random.choice(list(grid.keys()))
		exit_room = grid.cell(exit_room_key)
		exit_pos = Point(
				random.randrange(exit_room.left + 1, exit_room.right + 1 - 1),
				random.randrange(exit_room.top + 1, exit_room.bottom + 1 - 1),
				)
		if exit_room_key != enter_room_key:
			break
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	return start_pos, exit_pos, strata

def generate_single_pos(size):
	return Point(random.randrange(size.width), random.randrange(size.height))

def generate_pos(size, check=None, counter=1000):
	result = generate_single_pos(size)
	while counter > 0 and not check(result):
		result = generate_single_pos(size)
		counter -= 1
	return result

class BinarySpacePartition(object):
	def __init__(self, min_width=15, min_height=10):
		self.min_size = (min_width, min_height)
	def door_generator(self, room): # pragma: no cover
		""" Takes a Rect object and generates random Point for door position inside it.
		No need to determine wall facing and location, the algorithm would decide automatically.
		By default door is generated in random manner.
		"""
		x = random.randrange(room.left, room.right)
		y = random.randrange(room.top, room.bottom)
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
		topleft, bottomright = map(Point, (topleft, bottomright))
		Log.debug("topleft={0}, bottomright={1}".format(topleft, bottomright))
		too_narrow = abs(topleft.x - bottomright.x) <= self.min_size[0]
		too_low = abs(topleft.y - bottomright.y) <= self.min_size[1]
		if too_narrow and too_low:
			return
		horizontal = False if too_narrow else (True if too_low else self.hor_ver_generator())
		new_topleft = Point(topleft.x + 2, topleft.y + 2)
		userspace = Rect(
				new_topleft,
				bottomright - new_topleft + Point(1, 1),
				)
		if userspace.width <= 0 or userspace.height <= 0:
			return
		if userspace.width <= 1 or userspace.height <= 1: # TODO why is it needed?
			return
		door = self.door_generator(userspace)
		assert userspace.contains(door, with_border=True), "Door {0} not in room user space {1}".format(door, userspace)
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
		self.field.fill(topleft, bottomright, self.free())
		if is_horizontal:
			the_divide = door_pos.x
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell(Point(the_divide, y), self.obstacle())
		else:
			the_divide = door_pos.y
			for x in range(topleft.x, bottomright.x + 1):
				self.field.set_cell(Point(x, the_divide), self.obstacle())
		self.field.set_cell(door_pos, self.door())

def build_bsp_dungeon(size):
	size = Size(size)
	strata = Matrix(size, Cell(' ', False))

	Log.debug("Building surrounding walls.")
	for x in range(size.width):
		strata.set_cell((x, 0), Cell('#', False))
		strata.set_cell((x, size.height - 1), Cell('#', False))
	for y in range(size.height):
		strata.set_cell((0, y), Cell('#', False))
		strata.set_cell((size.width - 1, y), Cell('#', False))

	Log.debug("Running BSP...")
	bsp = BinarySpacePartition()
	builder = BSPBuilder(strata,
							 free=lambda: Cell('.'),
							 obstacle=lambda: Cell('#', False),
							 door=lambda: Cell('.'),
					 )
	for splitter in bsp.generate(Point(1, 1), Point(size.width - 2, size.height - 2)):
		Log.debug("Splitter: {0}".format(splitter))
		builder.fill(*splitter)

	floor_only = lambda pos: strata.cell(pos).passable
	start_pos = generate_pos(size, floor_only)
	Log.debug("Generated player pos: {0}".format(start_pos))

	exit_pos = generate_pos(size, lambda pos: floor_only(pos) and pos != start_pos)
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	return start_pos, exit_pos, strata

def build_cave(size):
	size = Size(size)
	strata = Matrix(size, 0)
	for x in range(1, strata.width - 1):
		for y in range(1, strata.height - 1):
			strata.set_cell((x, y), 0 if random.random() < 0.50 else 1)
	Log.debug("Initial state:\n{0}".format(strata.tostring()))

	new_layer = Matrix(strata)
	drop_wall_2_at = 4
	for step in range(drop_wall_2_at+1):
		for x in range(1, strata.width - 1):
			for y in range(1, strata.height - 1):
				neighs = set(clckwrkbdgr.math.get_neighbours(strata, (x, y), with_diagonal=True))
				neighs2 = set(itertools.chain.from_iterable(
					clckwrkbdgr.math.get_neighbours(strata, n, with_diagonal=True)
					for n in neighs
					)) - set(Point(x, y))
				wall_count = sum(int(strata.cell(n) == 0) for n in neighs)
				wall_2_count = sum(int(strata.cell(n) == 0) for n in neighs2)
				is_wall = strata.cell((x, y)) == 0
				if wall_count >= 5:
					new_layer.set_cell((x, y), 0)
				elif step < drop_wall_2_at and wall_2_count <= 2:
					new_layer.set_cell((x, y), 0)
				else:
					new_layer.set_cell((x, y), 1)
		strata, new_layer = new_layer, strata
		Log.debug("Step {1}:\n{0}".format(strata.tostring(), step))
	
	cavern = next(pos for pos in strata if strata.cell(pos) == 1)
	caverns = []
	while cavern:
		area = clckwrkbdgr.math.algorithm.floodfill(
				cavern,
				spread_function=lambda p: [x for x in clckwrkbdgr.math.get_neighbours(strata, p) if strata.cell(x) == 1]
				)
		count = 0
		for point in area:
			count += 1
			strata.set_cell(point, 2 + len(caverns))
		caverns.append(count)
		Log.debug("Filling cavern #{1}:\n{0}".format(strata.tostring(), len(caverns)))
		cavern = next((pos for pos in strata if strata.cell(pos) == 1), None)
	max_cavern = 2 + caverns.index(max(caverns))
	for pos in strata:
		if strata.cell(pos) in [0, max_cavern]:
			continue
		strata.set_cell(pos, 0)
	Log.debug("Finalized cave:\n{0}".format(strata.tostring()))

	floor_only = lambda pos: strata.cell(pos) > 1
	start_pos = generate_pos(size, floor_only)
	exit_pos = generate_pos(size, lambda pos: floor_only(pos) and pos != start_pos)
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	strata = strata.transform(lambda cell: Cell('.') if cell else Cell('#', False))

	return start_pos, exit_pos, strata

# this changes the direction to go from the current square, to the next available
def RandomDirections():
	cDir = [Point(0, 0), Point(0, 0), Point(0, 0), Point(0, 0)]
	direction = random.randrange(4)
	if direction == 0:
		cDir[0].x = -1; cDir[1].x = 1
		cDir[2].y = -1; cDir[3].y = 1
	elif direction == 1:
		cDir[3].x = -1; cDir[2].x = 1
		cDir[1].y = -1; cDir[0].y = 1
	elif direction == 2:
		cDir[2].x = -1; cDir[3].x = 1
		cDir[0].y = -1; cDir[1].y = 1
	elif direction == 3:
		cDir[1].x = -1; cDir[0].x = 1
		cDir[3].y = -1; cDir[2].y = 1
	return cDir

def build_maze(size):
	size = Size(size)
	layout_size = size - Size(2, 2) # For walls.
	# Layout size should be odd (for connections between cells).
	if layout_size.width % 2 == 0:
		layout_size.width -= 1
	if layout_size.height % 2 == 0:
		layout_size.height -= 1
	layout = Matrix(layout_size, False)

	# 0 is the most random, randomisation gets lower after that
	# less randomisation means more straight corridors
	RANDOMISATION = 0

	intDone = 0
	while True:
		Log.debug("Done {0} cells:\n{1}".format(intDone, layout.tostring(lambda c:'.' if c else '#')))
		# this code is used to make sure the numbers are odd
		current = Point(
				random.randrange((layout_size.width // 2)) * 2,
				random.randrange((layout_size.height // 2)) * 2,
				)
		# first one is free!
		if intDone == 0:
			layout.set_cell(current, True)
		if layout.cell(current):
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
					new_cell = Point(0, 0)
					new_cell.x = current.x + (cDir[intDir].x * 2)
					new_cell.y = current.y + (cDir[intDir].y * 2)
					# check if the tile can be used
					if layout.valid(new_cell) and not layout.cell(new_cell):
						# create a path
						layout.set_cell(new_cell, True)
						# and the square inbetween
						layout.set_cell(current + cDir[intDir], True)
						# this is now the current square
						current = new_cell
						blnBlocked = False
						# increment paths created
						intDone = intDone + 1
						break
		if not ( intDone + 1 < ((layout_size.width + 1) * (layout_size.height + 1)) / 4):
			break

	strata = Matrix(size, Cell('#', False)) # FIXME
	for pos in layout:
		if layout.cell(pos):
			strata.set_cell(pos + Point(1, 1), Cell('.'))

	floor_only = lambda pos: strata.cell(pos).passable
	start_pos = generate_pos(size, floor_only)
	Log.debug("Generated player pos: {0}".format(start_pos))

	exit_pos = generate_pos(size, lambda pos: floor_only(pos) and pos != start_pos)
	Log.debug("Generated exit pos: {0}".format(exit_pos))

	return start_pos, exit_pos, strata

def main_loop(window):
	curses.curs_set(0)
	builders = [
			build_bsp_dungeon,
			build_rogue_dungeon,
			build_cave,
			build_maze,
			]
	savefile = xdg.save_state_path('dotrogue')/'rogue.sav'
	if savefile.exists():
		Log.debug('Loading savefile: {0}...'.format(savefile))
		data = savefile.read_text()
		savedata = jsonpickle.decode(data, keys=True)
		player, exit_pos, strata = savedata
		Log.debug('Loaded.')
	else:
		builder = random.choice(builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		player, exit_pos, strata = builder((80, 23))
	field_of_view = Matrix((21, 21), False)
	playing = True
	god_vision = False
	Log.debug('Starting playing...')
	alive = True
	while playing:
		Log.debug('Recalculating Field Of View.')
		field_of_view.clear(False)
		for pos in field_of_view:
			Log.debug('FOV pos: {0}'.format(pos))
			half_size = field_of_view.size // 2
			rel_pos = Point(half_size) - pos
			Log.debug('FOV rel pos: {0}'.format(rel_pos))
			if (rel_pos.x / half_size.width) ** 2 + (rel_pos.y / half_size.height) ** 2 <= 1:
				Log.debug('Is inside FOV ellipse.')
				Log.debug('Traversing line of sight: [0;0] -> {0}'.format(rel_pos))
				for inner_line_pos in bresenham(Point(0, 0), rel_pos):
					real_world_pos = player + inner_line_pos
					Log.debug('Line pos: {0}, real world pos: {1}'.format(inner_line_pos, real_world_pos))
					fov_pos = half_size + inner_line_pos
					Log.debug('Setting as visible: {0}'.format(fov_pos))
					cell = strata.cell(real_world_pos)
					field_of_view.set_cell(fov_pos, True)
					if not cell.passable:
						Log.debug('Not passable, stop: {0}'.format(repr(cell.sprite)))
						break
		Log.debug("Full FOV:\n{0}".format(field_of_view.tostring(lambda v: '*' if v else '.')))

		Log.debug('Redrawing interface.')
		Log.debug('Player at: {0}'.format(player))
		for row in range(strata.height):
			for col in range(strata.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				cell = strata.cell((col, row))
				rel_pos = Point(col, row) - player
				Log.debug('Relative pos: {0}'.format(rel_pos))

				is_visible = False
				fov_pos = rel_pos + Point(field_of_view.size // 2)
				Log.debug('Relative FOV pos: {0}'.format(fov_pos))
				if field_of_view.valid(fov_pos):
					is_visible = field_of_view.cell(fov_pos)
					Log.debug('Valid FOV pos, is visible: {0}'.format(is_visible))
				Log.debug('Visible: {0}'.format(is_visible))

				if is_visible or god_vision:
					window.addstr(1+row, col, cell.sprite)
				else:
					window.addstr(1+row, col, ' ')

		is_exit_visible = False
		exit_rel_pos = exit_pos - player
		exit_fov_pos = exit_rel_pos + Point(field_of_view.size // 2)
		if field_of_view.valid(exit_fov_pos):
			is_exit_visible = field_of_view.cell(exit_fov_pos)
		if is_exit_visible or god_vision:
			window.addstr(1+exit_pos.y, exit_pos.x, '>')

		window.addstr(1+player.y, player.x, '@')

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
			if player == exit_pos:
				builder = random.choice(builders)
				Log.debug('Building new dungeon: {0}...'.format(builder))
				player, exit_pos, strata = builder((80, 23))
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
			new_pos = player + shift
			if strata.valid(new_pos) and strata.cell(new_pos).passable:
				Log.debug('Shift is valid, updating player pos: {0}'.format(player))
				player = new_pos
	if alive:
		savedata = player, exit_pos, strata
		data = jsonpickle.encode(savedata, indent=2, keys=True)
		savefile.write_bytes(data.encode('utf-8', 'replace'))
	elif savefile.exists():
		savefile.unlink()

def cli():
	debug = '--debug' in sys.argv
	clckwrkbdgr.logging.init('rogue',
			debug=True,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			rewrite_file=not debug,
			stream=None,
			)
	Log.debug('started')
	curses.wrapper(main_loop)
	Log.debug('exited')

if __name__ == '__main__':
	cli()
