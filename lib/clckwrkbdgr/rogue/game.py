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

class Direction(Enum):
	""" NONE
	UP_LEFT
	UP
	UP_RIGHT
	LEFT
	RIGHT
	DOWN_LEFT
	DOWN
	DOWN_RIGHT
	"""

class Game(object):
	BUILDERS = [
			pcg.builders.BSPDungeon,
			pcg.builders.CityBuilder,
			pcg.builders.Sewers,
			pcg.builders.RogueDungeon,
			pcg.builders.CaveBuilder,
			pcg.builders.MazeBuilder,
			]
	SHIFT = {
			Direction.LEFT : Point(-1,  0),
			Direction.DOWN : Point( 0, +1),
			Direction.UP : Point( 0, -1),
			Direction.RIGHT : Point(+1,  0),
			Direction.UP_LEFT : Point(-1, -1),
			Direction.UP_RIGHT : Point(+1, -1),
			Direction.DOWN_LEFT : Point(-1, +1),
			Direction.DOWN_RIGHT : Point(+1, +1),
			}

	def __init__(self, rng_seed=None, dummy=False, builders=None):
		self.builders = builders or self.BUILDERS
		self.rng = RNG(rng_seed)
		self.god = God()
		self.field_of_view = math.FieldOfView(10)
		self.events = []
		if dummy:
			return
		self.build_new_strata()
	def get_viewport(self):
		return self.strata.size
	def get_sprite(self, x, y):
		if self.player.x == x and self.player.y == y:
			return '@'
		if self.exit_pos.x == x and self.exit_pos.y == y:
			if self.remembered_exit or self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
				return '>'

		cell = self.strata.cell(x, y)
		if self.field_of_view.is_visible(x, y) or self.god.vision:
			return cell.sprite
		elif cell.visited and cell.remembered:
			return cell.remembered
		return None
	def update_vision(self):
		for p in self.field_of_view.update(
				self.player,
				is_visible=lambda p: self.strata.valid(p) and self.strata.cell(p.x, p.y).passable
				):
			cell = self.strata.cell(p.x, p.y)
			if cell.visited:
				continue
			if p == self.exit_pos:
				self.events.append(p)
			cell.visited = True
		if self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
			self.remembered_exit = True
	def build_new_strata(self):
		builder = build_dungeon(self.rng.choice(self.builders), self.rng, Size(80, 23))
		self.player = builder.start_pos
		self.exit_pos = builder.exit_pos
		self.strata = builder.strata
		self.remembered_exit = False
		self.update_vision()
	def move(self, direction):
		shift = self.SHIFT[direction]
		Log.debug('Shift: {0}'.format(shift))
		new_pos = self.player + shift
		if not self.strata.valid(new_pos):
			return
		if self.god.noclip:
			passable = True
		else:
			passable = self.strata.cell(new_pos.x, new_pos.y).passable
		if not passable:
			return
		Log.debug('Shift is valid, updating player pos: {0}'.format(self.player))
		self.player = new_pos
		self.update_vision()
	def jump_to(self, new_pos):
		self.player = new_pos
		self.update_vision()
	def descend(self):
		if self.player != self.exit_pos:
			return
		self.build_new_strata()

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
		game.update_vision()
		Log.debug('Loaded.')
		Log.debug(repr(game.strata))
		Log.debug('Player: {0}'.format(game.player))
	else:
		game = Game()
	playing = True
	aim = None
	autoexploring = False
	movement_queue = []
	Log.debug('Starting playing...')
	alive = True
	while playing:
		Log.debug('Redrawing interface.')
		Log.debug('Player at: {0}'.format(game.player))
		viewport = game.get_viewport()
		for row in range(viewport.height):
			for col in range(viewport.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				sprite = game.get_sprite(col, row)
				window.addstr(1+row, col, sprite or ' ')

		status = []
		if movement_queue:
			status.append('[auto]')
		if game.god.vision:
			status.append('[vis]')
		if game.god.noclip:
			status.append('[clip]')
		window.addstr(24, 0, (' '.join(status) + " " * 80)[:80])

		if aim:
			window.move(1+aim.y, aim.x)
		window.refresh()

		new_objects_in_fov = False
		while game.events:
			event = game.events.pop()
			new_objects_in_fov = True

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
			game.jump_to(new_pos)
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
				game.god.vision = not game.god.vision
			elif control == ord('c'):
				game.god.noclip = not game.god.noclip
		elif control == ord('Q'):
			Log.debug('Suicide.')
			alive = False
			playing = False
			break
		elif not aim and control == ord('>'):
			game.descend()
		elif chr(control) in 'hjklyubn':
			Log.debug('Moving.')
			if aim:
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
				new_pos = aim + shift
				if game.strata.valid(new_pos):
					aim = new_pos
			else:
				direction = {
					'h' : Direction.LEFT,
					'j' : Direction.DOWN,
					'k' : Direction.UP,
					'l' : Direction.RIGHT,
					'y' : Direction.UP_LEFT,
					'u' : Direction.UP_RIGHT,
					'b' : Direction.DOWN_LEFT,
					'n' : Direction.DOWN_RIGHT,
					}[chr(control)]
				game.move(direction)
	if alive:
		savefile.save(game)
	else:
		savefile.unlink()

def run(): # pragma: no cover
	curses.wrapper(main_loop)
