import os
from collections import namedtuple
from . import pcg
from .pcg import RNG
from . import math
from .utils import Enum
from .math import Point, Matrix, Size
from . import messages
from .messages import Log
from .ui import Action
from . import monsters

class Version(Enum):
	""" INITIAL
	PERSISTENT_RNG
	TERRAIN_TYPES
	MONSTERS
	MONSTER_BEHAVIOR
	"""

class Terrain(object):
	def __init__(self, sprite, passable=True, remembered=None, allow_diagonal=True, dark=False):
		self.sprite = sprite
		self.passable = passable
		self.remembered = remembered
		self.allow_diagonal = allow_diagonal
		self.dark = dark

class Cell(object):
	def __init__(self, terrain, visited=False):
		self.terrain = terrain
		self.visited = visited

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
	class AutoMovementStopped(BaseException): pass

	BUILDERS = [
			pcg.builders.BSPDungeon,
			pcg.builders.CityBuilder,
			pcg.builders.Sewers,
			pcg.builders.RogueDungeon,
			pcg.builders.CaveBuilder,
			pcg.builders.MazeBuilder,
			]
	SETTLERS = [
			pcg.settlers.SingleMonster,
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
	TERRAIN = {
			None : Terrain(' ', False),
			'corner' : Terrain("+", False, remembered='+'),
			'door' : Terrain("+", True, remembered='+'),
			'rogue_door' : Terrain("+", True, remembered='+', allow_diagonal=False, dark=True),
			'floor' : Terrain(".", True),
			'tunnel_floor' : Terrain(".", True, allow_diagonal=False),
			'passage' : Terrain("#", True, remembered='#'),
			'rogue_passage' : Terrain("#", True, remembered='#', allow_diagonal=False, dark=True),
			'wall' : Terrain('#', False, remembered='#'),
			'wall_h' : Terrain("-", False, remembered='-'),
			'wall_v' : Terrain("|", False, remembered='|'),
			'water' : Terrain("~", True),
			}
	SPECIES = {
			'player' : monsters.Species('player', "@", 10),
			'monster' : monsters.Species('monster', "M", 3),
			}

	def __init__(self, rng_seed=None, dummy=False, builders=None, settlers=None):
		self.builders = builders or self.BUILDERS
		self.settlers = settlers or self.SETTLERS
		self.rng = RNG(rng_seed)
		self.god = God()
		self.field_of_view = math.FieldOfView(10)
		self.autoexploring = False
		self.movement_queue = []
		self.monsters = []
		self.visible_monsters = []
		self.events = []
		if dummy:
			return
		self.build_new_strata()
	def main_loop(self, ui):
		playing = True
		Log.debug('Starting playing...')
		while playing:
			ui.redraw(self)

			try:
				if self.perform_automovement():
					if ui.user_interrupted():
						self.stop_automovement()
					continue
			except Game.AutoMovementStopped:
				continue

			action, action_data = ui.user_action(self)
			self.clear_event() # If we acted - we've seen all the events.
			if action == Action.NONE:
				pass
			elif action == Action.EXIT:
				playing = False
			elif action == Action.SUICIDE:
				self.get_player().hp = 0
				playing = False
			elif action == Action.WALK_TO:
				self.walk_to(action_data)
			elif action == Action.AUTOEXPLORE:
				self.start_autoexploring()
			elif action == Action.GOD_TOGGLE_VISION:
				self.god.vision = not self.god.vision
			elif action == Action.GOD_TOGGLE_NOCLIP:
				self.god.noclip = not self.god.noclip
			elif action == Action.DESCEND:
				self.descend()
			elif action == Action.MOVE:
				self.move(action_data)
	def get_viewport(self):
		return self.strata.size
	def tostring(self, with_fov=False):
		size = self.get_viewport()
		result = ""
		if not with_fov:
			old_god_vision = self.god.vision
			self.god.vision = True
		for y in range(size.height):
			for x in range(size.width):
				result += self.get_sprite(x, y) or ' '
			result += "\n"
		if not with_fov:
			self.god.vision = old_god_vision
		return result
	def get_sprite(self, x, y):
		monster = self.find_monster(x, y)
		if monster:
			if monster.pos.x == x and monster.pos.y == y:
				if self.field_of_view.is_visible(x, y) or self.god.vision:
					return monster.species.sprite
		if self.exit_pos.x == x and self.exit_pos.y == y:
			if self.god.vision or self.remembered_exit or self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
				return '>'

		cell = self.strata.cell(x, y)
		if self.field_of_view.is_visible(x, y) or self.god.vision:
			return cell.terrain.sprite
		elif cell.visited and cell.terrain.remembered:
			return cell.terrain.remembered
		return None
	def is_transparent(self, p):
		if not self.strata.valid(p):
			return False
		if not self.strata.cell(p.x, p.y).terrain.passable:
			return False
		if self.strata.cell(p.x, p.y).terrain.dark:
			player = self.get_player()
			if max(abs(player.pos.x - p.x), abs(player.pos.y - p.y)) >= 1:
				return False
		return True
	def update_vision(self):
		current_visible_monsters = []
		for p in self.field_of_view.update(
				self.get_player().pos,
				is_transparent=self.is_transparent,
				):
			cell = self.strata.cell(p.x, p.y)

			for monster in self.monsters:
				if monster.behavior == monsters.Behavior.PLAYER:
					continue
				if p == monster.pos:
					if monster not in self.visible_monsters:
						self.events.append(messages.DiscoverEvent(monster))
					current_visible_monsters.append(monster)

			if cell.visited:
				continue
			if p == self.exit_pos:
				self.events.append(messages.DiscoverEvent('>'))
			cell.visited = True
		self.visible_monsters = current_visible_monsters
		if self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
			self.remembered_exit = True
	def clear_event(self, event=None):
		if event is None:
			self.events[:] = []
		else:
			self.events.remove(event)
	def build_new_strata(self):
		builder = self.rng.choice(self.builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		Log.debug('With RNG: {0}...'.format(self.rng.value))
		builder = builder(self.rng, Size(80, 23))
		builder.build()
		for pos in builder.strata.size:
			builder.strata.set_cell(
					pos.x, pos.y,
					Cell(self.TERRAIN[builder.strata.cell(pos.x, pos.y)]),
					)

		settler = self.rng.choice(self.settlers)
		Log.debug("Populating dungeon: {0}".format(settler))
		settler = settler(self.rng, builder)
		settler.populate()
		self.monsters[:] = [
				monsters.Monster(self.SPECIES['player'], pcg.settlers.Behavior.PLAYER, builder.start_pos),
				]
		for monster_data in settler.monsters:
			species, monster_data = monster_data[0], monster_data[1:]
			monster_data = (self.SPECIES[species],) + monster_data
			self.monsters.append(monsters.Monster(*monster_data))

		Log.debug("Finalizing dungeon...")
		self.exit_pos = builder.exit_pos
		self.strata = builder.strata
		self.remembered_exit = False
		self.update_vision()
		Log.debug("Dungeon is ready.")
	def allow_movement_direction(self, from_point, to_point):
		shift = to_point - from_point
		is_diagonal = abs(shift.x) + abs(shift.y) == 2
		if not is_diagonal:
			return True
		if not self.strata.cell(from_point.x, from_point.y).terrain.allow_diagonal:
			return False
		if not self.strata.cell(to_point.x, to_point.y).terrain.allow_diagonal:
			return False
		return True
	def get_player(self):
		return next(monster for monster in self.monsters if monster.behavior == pcg.settlers.Behavior.PLAYER)
	def move(self, direction):
		shift = self.SHIFT[direction]
		Log.debug('Shift: {0}'.format(shift))
		new_pos = self.get_player().pos + shift
		if not self.strata.valid(new_pos):
			return False
		if self.god.noclip:
			passable = True
		else:
			passable = self.strata.cell(new_pos.x, new_pos.y).terrain.passable
		if not passable:
			return False
		if not self.allow_movement_direction(self.get_player().pos, new_pos):
			return False
		monster = self.find_monster(new_pos.x, new_pos.y)
		if monster:
			Log.debug('Monster at dest pos {0}: '.format(new_pos, monster))
			self.attack(self.get_player(), monster)
			return True
		Log.debug('Shift is valid, updating player pos: {0}'.format(self.get_player().pos))
		self.get_player().pos = new_pos
		self.update_vision()
		return True
	def attack(self, actor, target):
		self.events.append(messages.AttackEvent(actor, target))
		diff = -1
		target.hp += diff
		self.events.append(messages.HealthEvent(target, diff))
		if target.hp <= 0:
			self.events.append(messages.DeathEvent(target))
			self.monsters.remove(target)
	def find_monster(self, x, y):
		for monster in self.monsters:
			if monster.pos.x == x and monster.pos.y == y:
				return monster
		return None
	def jump_to(self, new_pos):
		self.get_player().pos = new_pos
		self.update_vision()
	def descend(self):
		if self.get_player().pos != self.exit_pos:
			return
		self.build_new_strata()
	def find_path(self, start, find_target):
		path = math.find_path(
				self.strata, start,
				is_passable=lambda p, from_point: self.strata.cell(p.x, p.y).terrain.passable and self.strata.cell(p.x, p.y).visited and self.allow_movement_direction(from_point, p),
				find_target=find_target,
				)
		if not path:
			return None
		if path[0] == self.get_player().pos: # We're already standing there.
			path.pop(0)
		return path
	def walk_to(self, dest):
		path = self.find_path(self.get_player().pos,
				find_target=lambda wave: dest if dest in wave else None,
				)
		if path:
			self.movement_queue.extend(path)
	def start_autoexploring(self):
		path = self.find_path(self.get_player().pos,
			find_target=lambda wave: next((target for target in sorted(wave)
			if any(
				not self.strata.cell(p.x, p.y).visited
				for p in self.strata.get_neighbours(target.x, target.y, with_diagonal=True)
				)
			), None),
			)
		if not path:
			return False
		self.movement_queue.extend(path)
		self.autoexploring = True
		return True
	def perform_automovement(self):
		if not self.movement_queue:
			return False
		if self.events:
			Log.debug('New events in FOV, aborting auto-moving mode.')
			return self.stop_automovement()
		Log.debug('Performing queued actions.')
		new_pos = self.movement_queue.pop(0)
		self.jump_to(new_pos)
		if self.movement_queue:
			return True
		if self.autoexploring:
			if not self.start_autoexploring():
				self.autoexploring = False
				raise Game.AutoMovementStopped()
		else:
			raise Game.AutoMovementStopped()
		return True
	def stop_automovement(self):
		self.movement_queue[:] = []
		self.autoexploring = False
		raise Game.AutoMovementStopped()

def save_game(game):
	dump_str = lambda _value: _value if _value is None else _value
	dump_bool = lambda _value: int(_value)
	yield game.exit_pos.x
	yield game.exit_pos.y
	yield dump_bool(game.remembered_exit)
	yield game.strata.size.width
	yield game.strata.size.height
	for cell in game.strata.cells:
		yield next(name for name, terrain in game.TERRAIN.items() if terrain is cell.terrain)
		yield dump_bool(cell.visited)
	yield len(game.monsters)
	for monster in game.monsters:
		yield next(name for name, species in game.SPECIES.items() if species is monster.species)
		yield monster.behavior
		yield monster.pos.x
		yield monster.pos.y
		yield monster.hp

def load_game(game, version, data):
	parse_str = lambda _value: _value if _value != 'None' else None
	parse_bool = lambda _value: _value == '1'

	legacy_player = None
	if version <= Version.MONSTERS:
		legacy_player = monsters.Monster(game.SPECIES['player'], pcg.settlers.Behavior.PLAYER, Point(int(next(data)), int(next(data))))
	exit_pos = Point(int(next(data)), int(next(data)))
	remembered_exit = parse_bool(next(data))

	strata_size = Size(int(next(data)), int(next(data)))
	strata = Matrix(strata_size, None)
	if version > Version.TERRAIN_TYPES:
		for _ in range(strata_size.width * strata_size.height):
			strata.cells[_] = Cell(game.TERRAIN[parse_str(next(data))])
			strata.cells[_].visited = parse_bool(next(data))
	else:
		for _ in range(strata_size.width * strata_size.height):
			cell_type = parse_str(next(data)), parse_bool(next(data)), parse_str(next(data))
			for terrain in game.TERRAIN:
				if game.TERRAIN[terrain].sprite == cell_type[0] \
					and game.TERRAIN[terrain].passable == cell_type[1] \
					and game.TERRAIN[terrain].remembered == cell_type[2]:
					break
			strata.cells[_] = Cell(game.TERRAIN[terrain])
			strata.cells[_].visited = parse_bool(next(data))
	if legacy_player:
		game.monsters.append(legacy_player)
	if version > Version.MONSTERS:
		count = int(next(data))
		for _ in range(count):
			species_name = next(data)
			species = game.SPECIES[species_name]
			if version > Version.MONSTER_BEHAVIOR:
				behavior = int(next(data))
			else:
				if species_name == 'player':
					behavior = pcg.settlers.Behavior.PLAYER
				else:
					behavior = pcg.settlers.Behavior.ANGRY
			pos = Point(int(next(data)), int(next(data)))
			monster = monsters.Monster(species, behavior, pos)
			monster.hp = int(next(data))
			game.monsters.append(monster)

	game.exit_pos = exit_pos
	game.strata = strata
	game.remembered_exit = remembered_exit

class God:
	def __init__(self):
		self.vision = False
		self.noclip = False

class Savefile:
	FILENAME = os.path.expanduser('~/.rogue.sav')
	@classmethod
	def last_save_time(cls):
		if not os.path.exists(cls.FILENAME):
			return 0
		return os.stat(cls.FILENAME).st_mtime
	def load(self):
		if not os.path.exists(self.FILENAME):
			return None
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

def run():
	savefile = Savefile()
	game = savefile.load()
	if game is not None:
		game.update_vision()
		Log.debug('Loaded.')
		Log.debug(repr(game.strata))
		Log.debug('Player: {0}'.format(game.get_player()))
	else:
		game = Game()
	from .ui import auto_ui
	with auto_ui()() as ui:
		game.main_loop(ui)
	if game.get_player().is_alive():
		savefile.save(game)
	else:
		savefile.unlink()
