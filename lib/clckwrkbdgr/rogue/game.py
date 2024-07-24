import os
from collections import namedtuple
import curses
from . import pcg
from .pcg import RNG
from . import math
from .utils import Enum
from .math import Point, Matrix, Size
from .messages import Log

class Version(Enum):
	""" INITIAL
	PERSISTENT_RNG
	"""

class Cell(object):
	def __init__(self, sprite, passable=True, remembered=None):
		self.sprite = sprite
		self.passable = passable
		self.remembered = remembered
		self.visited = False

class Game(object):
	BUILDERS = [
			pcg.builders.BSPDungeon,
			pcg.builders.CityBuilder,
			pcg.builders.Sewers,
			pcg.builders.RogueDungeon,
			pcg.builders.CaveBuilder,
			pcg.builders.MazeBuilder,
			]

	def __init__(self, rng_seed=None, dummy=False):
		self.rng = RNG(rng_seed)
		if dummy:
			return
		self.build_new_strata()
	def build_new_strata(self):
		builder = build_dungeon(self.rng.choice(Game.BUILDERS), self.rng, Size(80, 23))
		self.player = builder.start_pos
		self.exit_pos = builder.exit_pos
		self.strata = builder.strata
		self.remembered_exit = False

def save_game(game):
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

def load_game(game, version, data):
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

	game.player = player
	game.exit_pos = exit_pos
	game.strata = strata
	game.remembered_exit = remembered_exit

class God: # pragma: no cover -- TODO
	def __init__(self):
		self.vision = False
		self.noclip = False

def build_dungeon(builder, rng, size):
	Log.debug('Building dungeon: {0}...'.format(builder))
	Log.debug('With RNG: {0}...'.format(rng.value))
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

def autoexplore(start, strata):
	return math.find_path(
			strata, start,
			is_passable=lambda p: strata.cell(p.x, p.y).passable and strata.cell(p.x, p.y).visited,
			find_target=lambda wave: next((target for target in sorted(wave)
			if any(
				not strata.cell(p.x, p.y).visited
				for p in strata.get_neighbours(target.x, target.y, with_diagonal=True)
				)
			), None),
			)

class Savefile:
	FILENAME = os.path.expanduser('~/.rogue.sav')
	def load(self):
		if not os.path.exists(self.FILENAME):
			return None, None
		Log.debug('Loading savefile: {0}...'.format(self.FILENAME))
		with open(self.FILENAME, 'r') as f:
			data = f.read().split('\0')
		data = iter(data)
		version = int(next(data))
		rng_seed = None
		if version > Version.PERSISTENT_RNG:
			rng_seed = int(next(data))
		game = Game(rng_seed, dummy=True)
		load_game(game, version, data)
		return game
	def save(self, game):
		dump = save_game(game)
		with open(self.FILENAME, 'w') as f:
			f.write(str(Version.CURRENT) + '\0')
			f.write(str(game.rng.value) + '\0')
			f.write('\0'.join(map(str, dump)))
	def unlink(self):
		if not os.path.exists(self.FILENAME):
			return
		os.unlink(self.FILENAME)

def main_loop(window): # pragma: no cover -- TODO
	curses.curs_set(0)
	savefile = Savefile()
	game = savefile.load()
	if game is not None:
		Log.debug('Loaded.')
		Log.debug(repr(game.strata))
		Log.debug('Player: {0}'.format(game.player))
	else:
		game = Game()
	field_of_view = math.FieldOfView(10)
	playing = True
	aim = None
	autoexploring = False
	movement_queue = []
	god = God()
	Log.debug('Starting playing...')
	alive = True
	while playing:
		new_objects_in_fov = []
		visible_cells = set()
		for p in field_of_view.update(
				game.player,
				is_visible=lambda p: game.strata.valid(p) and game.strata.cell(p.x, p.y).passable
				):
			cell = game.strata.cell(p.x, p.y)
			if not cell.visited:
				if p == game.exit_pos:
					new_objects_in_fov.append(p)
			cell.visited = True
			visible_cells.add(p)

		Log.debug('Redrawing interface.')
		Log.debug('Player at: {0}'.format(game.player))
		for row in range(game.strata.size.height):
			for col in range(game.strata.size.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				cell = game.strata.cell(col, row)
				is_visible = Point(col, row) in visible_cells
				if is_visible or god.vision:
					window.addstr(1+row, col, cell.sprite)
				elif cell.visited and cell.remembered:
					window.addstr(1+row, col, cell.remembered)
				else:
					window.addstr(1+row, col, ' ')

		is_exit_visible = game.exit_pos in visible_cells
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
			path = math.find_path(
					game.strata, game.player,
					is_passable=lambda p: strata.cell(p.x, p.y).passable and strata.cell(p.x, p.y).visited,
					find_target=lambda wave: aim if aim in wave else None,
					)
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
				game.make_new_strata()
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
		savefile.save(game)
	else:
		savefile.unlink()

def run(): # pragma: no cover
	curses.wrapper(main_loop)
