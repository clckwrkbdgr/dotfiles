import copy
import random
from collections import namedtuple
import curses
from clckwrkbdgr.math import Point, Matrix, Size, Rect
import clckwrkbdgr.math.graph

Cell = namedtuple('Cell', 'sprite passable')

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

	return start_pos, strata

def main_loop(window):
	curses.curs_set(0)
	player, strata = build_rogue_dungeon((80, 23))
	playing = True
	while playing:
		for row in range(strata.height):
			for col in range(strata.width):
				window.addstr(1+row, col, strata.cell((col, row)).sprite)
		window.addstr(1+player.y, player.x, '@')
		window.refresh()

		control = window.getch()
		if control == ord('q'):
			playing = False
			break
		elif chr(control) in 'hjklyubn':
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
			new_pos = player + shift
			if strata.valid(new_pos) and strata.cell(new_pos).passable:
				player = new_pos

def cli():
	curses.wrapper(main_loop)

if __name__ == '__main__':
	cli()
