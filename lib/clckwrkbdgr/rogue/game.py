import os
from collections import namedtuple
import curses
from . import pcg
from .pcg import RNG
from . import math
from .math import Point, Matrix, Size
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

class God: # pragma: no cover -- TODO
	def __init__(self):
		self.vision = False
		self.noclip = False

def build_dungeon(builder, rng, size): # pragma: no cover -- TODO
	Log.debug('Building dungeon: {0}...'.format(builder))
	builder = builder(rng, size)
	builder.add_cell_type(None, Cell, ' ', False)
	builder.add_cell_type('corner', Cell, "+", False, remembered='+')
	builder.add_cell_type('door', Cell, "+", True, remembered='+')
	builder.add_cell_type('floor', Cell, ".", True)
	builder.add_cell_type('passage', Cell, "#", True, remembered='#')
	builder.add_cell_type('wall', Cell, '#', False, remembered='#')
	builder.add_cell_type('wall_h', Cell, "-", False, remembered='-')
	builder.add_cell_type('wall_v', Cell, "|", False, remembered='|')
	builder.add_cell_type('water', Cell, "~", True)
	builder.build()
	return builder

def find_path(start, target, strata): # pragma: no cover -- TODO
	def _reorder_links(_previous_node, _links):
		return sorted(_links, key=lambda p: abs(_previous_node.x - p.x) + abs(_previous_node.y - p.y))
	def _is_linked(_node_from, _node_to):
		return abs(_node_from.x - _node_to.x) <= 1 and abs(_node_from.y - _node_to.y) <= 1
	def _get_links(_node):
		return [p for p in strata.get_neighbours(
			_node.x, _node.y,
			with_diagonal=True,
			)
			 if strata.cell(p.x, p.y).passable and strata.cell(p.x, p.y).visited
			 ]
	waves = [{start}]
	already_used = set()
	depth = strata.size.width * strata.size.width * strata.size.height * strata.size.height
	while depth > 0:
		depth -= 1
		closest = set(node for previous in waves[-1] for node in _get_links(previous))
		new_wave = closest - already_used
		if not new_wave:
			return None
		if target in new_wave:
			path = [target]
			for wave in reversed(waves):
				path.insert(0, next(node for node in _reorder_links(path[0], wave) if _is_linked(node, path[0])))
			return path
		already_used |= new_wave
		waves.append(new_wave)

def autoexplore(start, strata): # pragma: no cover -- TODO
	def _reorder_links(_previous_node, _links):
		return sorted(_links, key=lambda p: abs(_previous_node.x - p.x) + abs(_previous_node.y - p.y))
	def _is_linked(_node_from, _node_to):
		return abs(_node_from.x - _node_to.x) <= 1 and abs(_node_from.y - _node_to.y) <= 1
	def _get_links(_node):
		return [p for p in strata.get_neighbours(
			_node.x, _node.y,
			with_diagonal=True,
			)
			 if strata.cell(p.x, p.y).passable and strata.cell(p.x, p.y).visited
			 ]
	waves = [{start}]
	already_used = set()
	depth = strata.size.width * strata.size.width * strata.size.height * strata.size.height
	while depth > 0:
		depth -= 1
		closest = set(node for previous in waves[-1] for node in _get_links(previous))
		new_wave = closest - already_used
		if not new_wave:
			return None
		for target in new_wave:
			neighs = strata.get_neighbours(target.x, target.y, with_diagonal=True)
			for p in neighs:
				if not strata.cell(p.x, p.y).visited:
					break
			else:
				continue

			path = [target]
			for wave in reversed(waves):
				path.insert(0, next(node for node in _reorder_links(path[0], wave) if _is_linked(node, path[0])))
			return path
		already_used |= new_wave
		waves.append(new_wave)

def main_loop(window): # pragma: no cover -- TODO
	curses.curs_set(0)
	rng = RNG()
	builders = [
			pcg.builders.BSPDungeon,
			pcg.builders.CityBuilder,
			pcg.builders.Sewers,
			pcg.builders.RogueDungeon,
			pcg.builders.CaveBuilder,
			pcg.builders.MazeBuilder,
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
		builder = build_dungeon(rng.choice(builders), rng, Size(80, 23))
		game = Game(builder.start_pos, builder.exit_pos, builder.strata)
	field_of_view = Matrix(Size(21, 21), False)
	playing = True
	aim = None
	autoexploring = False
	movement_queue = []
	god = God()
	Log.debug('Starting playing...')
	alive = True
	while playing:
		Log.debug('Recalculating Field Of View.')
		field_of_view.clear(False)
		new_objects_in_fov = []
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
				for inner_line_pos in math.bresenham(Point(0, 0), rel_pos):
					real_world_pos = game.player + inner_line_pos
					Log.debug('Line pos: {0}, real world pos: {1}'.format(inner_line_pos, real_world_pos))
					fov_pos = Point(half_size.width + inner_line_pos.x,
							half_size.height + inner_line_pos.y,
							)
					if not game.strata.valid(real_world_pos):
						continue
					Log.debug('Setting as visible: {0}'.format(fov_pos))
					cell = game.strata.cell(real_world_pos.x, real_world_pos.y)
					if not cell.visited:
						if real_world_pos == game.exit_pos:
							new_objects_in_fov.append(real_world_pos)
					cell.visited = True
					field_of_view.set_cell(fov_pos.x, fov_pos.y, True)
					if not cell.passable:
						Log.debug('Not passable, stop: {0}'.format(repr(cell.sprite)))
						break
		Log.debug("Full FOV:\n{0}".format(repr(field_of_view)))

		Log.debug('Redrawing interface.')
		Log.debug('Player at: {0}'.format(game.player))
		for row in range(game.strata.size.height):
			for col in range(game.strata.size.width):
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

				if is_visible or god.vision:
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
		if is_exit_visible or god.vision or game.remembered_exit:
			window.addstr(1+game.exit_pos.y, game.exit_pos.x, '>')

		window.addstr(1+game.player.y, game.player.x, '@')

		status = []
		if movement_queue:
			status.append('[auto]')
		if god.vision:
			status.append('[vis]')
		if god.noclip:
			status.append('[clip]')
		window.addstr(24, 0, (' '.join(status) + " " * 80)[:80])

		if aim:
			window.move(1+aim.y, aim.x)
		window.refresh()

		if movement_queue:
			if new_objects_in_fov:
				Log.debug('New objects in FOV, aborting auto-moving mode.')
				movement_queue.clear()
				window.timeout(-1)
				window.nodelay(0)
				autoexploring = False
				continue
			Log.debug('Performing queued actions.')
			new_pos = movement_queue.pop(0)
			game.player = new_pos
			if movement_queue:
				window.nodelay(1)
				window.timeout(30)
				control = window.getch()
				if control != -1:
					movement_queue.clear()
					window.timeout(-1)
					window.nodelay(0)
					autoexploring = False
			else:
				if autoexploring:
					path = autoexplore(game.player, game.strata)
					if path:
						movement_queue.extend(path)
					else:
						window.timeout(-1)
						window.nodelay(0)
						autoexploring = False
				else:
					window.timeout(-1)
					window.nodelay(0)
			continue

		Log.debug('Performing user actions.')
		control = window.getch()
		Log.debug('Control: {0} ({1}).'.format(control, repr(chr(control))))
		if control == ord('q'):
			Log.debug('Exiting the game.')
			playing = False
			break
		elif control == ord('x'):
			if aim:
				aim = None
				curses.curs_set(0)
			else:
				aim = game.player
				curses.curs_set(1)
		elif aim and control == ord('.'):
			path = find_path(game.player, aim, game.strata)
			if path:
				movement_queue.extend(path)
			aim = None
			curses.curs_set(0)
		elif control == ord('o'):
			path = autoexplore(game.player, game.strata)
			if path:
				movement_queue.extend(path)
				autoexploring = True
		elif control == ord('~'):
			control = window.getch()
			if control == ord('v'):
				god.vision = not god.vision
			elif control == ord('c'):
				god.noclip = not god.noclip
		elif control == ord('Q'):
			Log.debug('Suicide.')
			alive = False
			playing = False
			break
		elif not aim and control == ord('>'):
			if game.player == game.exit_pos:
				builder = build_dungeon(rng.choice(builders), rng, Size(80, 23))
				game = Game(builder.start_pos, builder.exit_pos, builder.strata)
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
			if aim:
				new_pos = aim + shift
				if game.strata.valid(new_pos):
					aim = new_pos
			else:
				new_pos = game.player + shift
				if game.strata.valid(new_pos):
					if god.noclip:
						passable = True
					else:
						passable = game.strata.cell(new_pos.x, new_pos.y).passable
					if passable:
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
