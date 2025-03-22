import functools
import random
import math
import string
from collections import namedtuple
import curses, curses.ascii
from clckwrkbdgr.math import Point, Rect, Size, Matrix, sign
from clckwrkbdgr import xdg

MOVEMENT = {
		'h' : Point(-1, 0),
		'j' : Point(0, 1),
		'k' : Point(0, -1),
		'l' : Point(1, 0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),
		}

Sprite = namedtuple('Sprite', 'sprite color')
COLORS = {}

def init_colors():
	for i in range(8):
		curses.init_pair(i + 1, i, curses.COLOR_BLACK)
	basic_colors = {
		'black' : curses.color_pair(curses.COLOR_BLACK + 1),
		'red' : curses.color_pair(curses.COLOR_RED + 1),
		'green' : curses.color_pair(curses.COLOR_GREEN + 1),
		'blue' : curses.color_pair(curses.COLOR_BLUE + 1),
		'yellow' : curses.color_pair(curses.COLOR_YELLOW + 1),
		'cyan' : curses.color_pair(curses.COLOR_CYAN + 1),
		'magenta' : curses.color_pair(curses.COLOR_MAGENTA + 1),
		'white' : curses.color_pair(curses.COLOR_WHITE + 1),
		}
	COLORS.update(basic_colors)
	COLORS.update({
		'bold_' + name : pair | curses.A_BOLD for name, pair in basic_colors.items()
		})

class Coord:
	def __init__(self, world_pos=None, zone_pos=None, field_pos=None):
		self.world = world_pos or Point(0, 0)
		self.zone = zone_pos or Point(0, 0)
		self.field = field_pos or Point(0, 0)
	def save(self, stream):
		stream.write(self.world.x)
		stream.write(self.world.y)
		stream.write(self.zone.x)
		stream.write(self.zone.y)
		stream.write(self.field.x)
		stream.write(self.field.y)
	def load(self, stream):
		self.world.x = stream.read(int)
		self.world.y = stream.read(int)
		self.zone.x = stream.read(int)
		self.zone.y = stream.read(int)
		self.field.x = stream.read(int)
		self.field.y = stream.read(int)
	def get_global(self, world):
		return Point(
				self.world.x * world.zone_size.width * world.field_size.width,
				self.world.y * world.zone_size.height * world.field_size.height,
				) + Point(
				self.zone.x * world.field_size.width,
				self.zone.y * world.field_size.height,
				) + self.field
	def __str__(self):
		return '{0:02X}.{1:X}.{2:X};{3:02X}.{4:X}.{5:X}'.format(
				self.world.x, self.zone.x, self.field.x,
				self.world.y, self.zone.y, self.field.y,
				)
	@classmethod
	def from_global(cls, pos, world):
		in_world = Point(
				pos.x // (world.zone_size.width * world.field_size.width),
				pos.y // (world.zone_size.height * world.field_size.height),
				)
		pos = Point(
				pos.x % (world.zone_size.width * world.field_size.width),
				pos.y % (world.zone_size.height * world.field_size.height),
				)
		in_zone = Point(
				pos.x // world.field_size.width,
				pos.y // world.field_size.height,
				)
		in_field = Point(
				pos.x % world.field_size.width,
				pos.y % world.field_size.height,
				)
		return cls(in_world, in_zone, in_field)

class Terrain:
	def __init__(self, sprite, passable=True):
		self.sprite = sprite
		self.passable = passable
	def save(self, stream):
		stream.write(self.sprite.sprite)
		stream.write(self.sprite.color)
		stream.write(int(self.passable))
	def load(self, stream):
		self.sprite = Sprite(stream.read(), stream.read())
		self.passable = bool(stream.read(int))

class Questgiver:
	def __init__(self):
		self.quest = None
		self.prepared_quest = None
	def save(self, stream):
		if self.quest:
			stream.write(self.quest[0])
			stream.write(self.quest[1])
			stream.write(self.quest[2])
		else:
			stream.write('')
		if self.prepared_quest:
			stream.write(self.prepared_quest[0])
			stream.write(self.prepared_quest[1])
			stream.write(self.prepared_quest[2])
		else:
			stream.write('')
	def load(self, stream):
		self.quest = stream.read()
		if self.quest:
			self.quest = (int(self.quest), stream.read(), stream.read(int))
		else:
			self.quest = None
		self.prepared_quest = stream.read()
		if self.prepared_quest:
			self.prepared_quest = (int(self.prepared_quest), stream.read(), stream.read(int))
		else:
			self.prepared_quest = None

class Monster:
	def __init__(self, pos, sprite, max_hp, behaviour=None):
		self.pos = pos
		self.sprite = sprite
		self.hp = self.max_hp = max_hp
		self.regeneration = 0
		self.behaviour = behaviour
		self.inventory = []
	def save(self, stream):
		if isinstance(self.pos, Coord):
			stream.write('|'.join((
				','.join(map(str, self.pos.world)),
				','.join(map(str, self.pos.zone)),
				','.join(map(str, self.pos.field)),
				)))
		else:
			stream.write(','.join(map(str, self.pos)))
		stream.write(self.sprite.sprite)
		stream.write(self.sprite.color)
		stream.write(self.hp)
		stream.write(self.max_hp)
		stream.write(self.regeneration)

		if self.behaviour is None:
			stream.write('')
		elif isinstance(self.behaviour, Questgiver):
			stream.write('quest')
			self.behaviour.save(stream)
		else:
			stream.write(self.behaviour)

		stream.write(len(self.inventory))
		for item in self.inventory:
			item.save(stream)
	def load(self, stream):
		pos = stream.read()
		if '|' in pos:
			parts = pos.split('|')
			parts = tuple(tuple(map(int, part.split(','))) for part in parts)
			self.pos = Coord(Point(*(parts[0])), Point(*(parts[1])), Point(*(parts[2])))
		else:
			self.pos.x, self.pos.y = map(int, pos.split(','))
		self.sprite = Sprite(stream.read(), stream.read())
		self.hp = stream.read(int)
		self.max_hp = stream.read(int)
		self.regeneration = stream.read(int)

		self.behaviour = stream.read()
		if self.behaviour == 'aggressive':
			pass
		elif self.behaviour == 'quest':
			self.behaviour = Questgiver()
			self.behaviour.load(stream)
		else:
			assert not self.behaviour, self.behaviour
			self.behaviour = None

		items = stream.read(int)
		for _ in range(items):
			item = Item(Point(0, 0), None, None)
			item.load(stream)
			self.inventory.append(item)

class Item:
	def __init__(self, pos, sprite, name):
		self.pos = pos
		self.sprite = sprite
		self.name = name
	def save(self, stream):
		if self.pos:
			stream.write(self.pos.x)
			stream.write(self.pos.y)
		else:
			stream.write(0)
			stream.write(0)
		stream.write(self.sprite.sprite)
		stream.write(self.sprite.color)
		stream.write(self.name)
	def load(self, stream):
		self.pos.x = stream.read(int)
		self.pos.y = stream.read(int)
		self.sprite = Sprite(stream.read(), stream.read())
		self.name = stream.read()

class Overworld:
	def __init__(self, size):
		self.zones = Matrix(size, None)
		self._valid_zone = None
	def save(self, stream):
		stream.write(self.zones.width)
		stream.write(self.zones.height)
		for zone_index in self.zones:
			zone = self.zones.cell(zone_index)
			if zone:
				stream.write('.')
				zone.save(stream)
			else:
				stream.write('')
	def load(self, stream):
		size = Size(stream.read(int), stream.read(int))
		self.zones = Matrix(size, None)
		for zone_index in self.zones:
			zone = stream.read()
			if not zone:
				continue
			zone = Zone(Size(1, 1), None)
			zone.load(stream)
			self.zones.set_cell(zone_index, zone)
			self._valid_zone = zone_index
	def add_zone(self, zone_pos, zone):
		self.zones.set_cell(zone_pos, zone)
		self._valid_zone = zone_pos
	@property
	def zone_size(self):
		return self.zones.cell(self._valid_zone).fields.size
	@property
	def field_size(self):
		return self.zones.cell(self._valid_zone).field_size
	@property
	def full_width(self):
		return self.zones.width * self.zone_size.width
	@property
	def full_height(self):
		return self.zones.height * self.zone_size.height
	def all_monsters(self, raw=False, zone_range=None):
		for zone_index in (zone_range or self.zones):
			zone = self.zones.cell(zone_index)
			if zone is None:
				continue
			for field_index in zone.fields:
				for monster in zone.fields.cell(field_index).monsters:
					coord = Coord(zone_index, field_index, monster.pos)
					if not raw:
						coord = coord.get_global(self)
					yield coord, monster

class Zone:
	def __init__(self, size, default_tile):
		self.fields = Matrix(size, default_tile)
	def save(self, stream):
		stream.write(self.fields.width)
		stream.write(self.fields.height)
		for field_index in self.fields:
			field = self.fields.cell(field_index)
			field.save(stream)
	def load(self, stream):
		size = Size(stream.read(int), stream.read(int))
		self.fields = Matrix(size, None)
		for field_index in self.fields:
			field = Field(Size(1, 1), None)
			field.load(stream)
			self.fields.set_cell(field_index, field)
	@property
	@functools.lru_cache()
	def field_size(self):
		return self.fields.cell((0, 0)).tiles.size
	@property
	def full_width(self):
		return self.fields.width * self.field_size.width
	@property
	def full_height(self):
		return self.fields.height * self.field_size.height

class Field:
	def __init__(self, size, default_tile):
		self.tiles = Matrix(size, default_tile)
		self.items = []
		self.monsters = []
	def save(self, stream):
		stream.write(self.tiles.width)
		stream.write(self.tiles.height)
		for tile_index in self.tiles:
			tile = self.tiles.cell(tile_index)
			tile.save(stream)

		stream.write(len(self.items))
		for item in self.items:
			item.save(stream)

		stream.write(len(self.monsters))
		for monster in self.monsters:
			monster.save(stream)
	def load(self, stream):
		size = Size(stream.read(int), stream.read(int))
		self.tiles = Matrix(size, None)
		for tile_index in self.tiles:
			tile = Terrain(Size(), None)
			tile.load(stream)
			self.tiles.set_cell(tile_index, tile)

		items = stream.read(int)
		for _ in range(items):
			item = Item(Point(0, 0), None, None)
			item.load(stream)
			self.items.append(item)

		monsters = stream.read(int)
		for _ in range(monsters):
			monster = Monster(Point(0, 0), None, None)
			monster.load(stream)
			self.monsters.append(monster)

def generate_field():
	return random.choice([
		generate_forest,
		generate_desert,
		generate_thundra,
		generate_marsh,
		])()

def generate_forest():
	field = Field((16, 16), Terrain(Sprite('.', 'green')))
	forest_density = random.randrange(10) * 10
	for _ in range(forest_density):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('&', 'bold_green')))
	for _ in range(10):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('"', 'bold_green')))
	for _ in range(10):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('"', 'green')))
	return field

def generate_desert():
	field = Field((16, 16), Terrain(Sprite('.', 'bold_yellow')))
	for _ in range(random.randrange(3)):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('^', 'yellow'), passable=False))
	for _ in range(10):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('"', 'green')))
	return field

def generate_thundra():
	field = Field((16, 16), Terrain(Sprite('.', 'bold_white')))
	for _ in range(3 + random.randrange(3)):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('.', 'cyan')))
	for _ in range(3 + random.randrange(7)):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('.', 'white')))
	return field

def generate_marsh():
	field = Field((16, 16), Terrain(Sprite('~', 'cyan')))
	for _ in range(100):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('~', 'green')))
	for _ in range(random.randrange(100)):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('.', 'green')))
	for _ in range(random.randrange(5)):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('&', 'green')))
	for _ in range(random.randrange(10)):
		field.tiles.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('&', 'yellow')))
	return field

def add_building(field):
	building = Rect(
			Point(2 + random.randrange(3), 2 + random.randrange(3)),
			Size(6 + random.randrange(3), 6 + random.randrange(3)),
			)
	for x in range(building.width):
		for y in range(building.height):
			field.tiles.set_cell((building.left + x, building.top + y), Terrain(Sprite('.', 'white')))
	for x in range(building.width):
		field.tiles.set_cell((building.left + x, building.top), Terrain(Sprite('#', 'white'), passable=False))
		field.tiles.set_cell((building.left + x, building.bottom), Terrain(Sprite('#', 'white'), passable=False))
	for y in range(building.height):
		field.tiles.set_cell((building.left, building.top + y), Terrain(Sprite('#', 'white'), passable=False))
		field.tiles.set_cell((building.right, building.top + y), Terrain(Sprite('#', 'white'), passable=False))
	if random.randrange(2) == 0:
		door = building.top + 1 + random.randrange(building.height - 2)
		if random.randrange(2) == 0:
			field.tiles.set_cell((building.left, door), Terrain(Sprite('.', 'white')))
		else:
			field.tiles.set_cell((building.right, door), Terrain(Sprite('.', 'white')))
	else:
		door = building.left + 1 + random.randrange(building.width - 2)
		if random.randrange(2) == 0:
			field.tiles.set_cell((door, building.top), Terrain(Sprite('.', 'white')))
		else:
			field.tiles.set_cell((door, building.bottom), Terrain(Sprite('.', 'white')))
	dweller_pos = building.topleft + Point(1, 1) + Point(
			random.randrange(building.width - 2),
			random.randrange(building.height - 2),
			)
	colors = list(set(COLORS.keys()) - {'black', 'bold_white'})
	monster_color = random.choice(colors)
	dweller = Monster(
		dweller_pos,
		Sprite('@', monster_color),
		10,
		behaviour=Questgiver(),
		)
	field.monsters.append(dweller)

class Game:
	def __init__(self):
		self.player = Monster(Coord(), Sprite('@', 'bold_white'), 10)
		self.world = Overworld((256, 256))
		self.passed_time = 0
	def save(self, stream):
		self.player.save(stream)
		self.world.save(stream)
		stream.write(self.passed_time)
	def load(self, stream):
		self.player.load(stream)
		self.world.load(stream)
		self.passed_time = stream.read(int)
	def generate(self):
		zone_pos = Point(
				random.randrange(self.world.zones.size.width),
				random.randrange(self.world.zones.size.height),
				)
		self.player.pos.world = zone_pos
		self.generate_zone(zone_pos)
	def autoexpand(self, coord, margin):
		pos = coord.get_global(self.world)
		within_zone = Point(
				pos.x % (self.world.zone_size.width * self.world.field_size.width),
				pos.y % (self.world.zone_size.height * self.world.field_size.height),
				)
		close_to_zone_boundaries = False
		expansion = Point(0, 0)
		if within_zone.x - 40 < 0:
			close_to_zone_boundaries = True
			expansion.x = -1
		if within_zone.x + 40 >= self.world.zones.cell(coord.world).full_width:
			close_to_zone_boundaries = True
			expansion.x = +1
		if within_zone.y - 40 < 0:
			close_to_zone_boundaries = True
			expansion.y = -1
		if within_zone.y + 40 >= self.world.zones.cell(coord.world).full_height:
			close_to_zone_boundaries = True
			expansion.y = +1
		if not close_to_zone_boundaries:
			return
		if expansion.x:
			new_pos = coord.world + Point(expansion.x, 0)
			if self.world.zones.valid(new_pos) and self.world.zones.cell(new_pos) is None:
				self.generate_zone(new_pos)
		if expansion.y:
			new_pos = coord.world + Point(0, expansion.y)
			if self.world.zones.valid(new_pos) and self.world.zones.cell(new_pos) is None:
				self.generate_zone(new_pos)
		if expansion.x * expansion.y:
			new_pos = coord.world + expansion
			if self.world.zones.valid(new_pos) and self.world.zones.cell(new_pos) is None:
				self.generate_zone(new_pos)
	def generate_zone(self, zone_pos):
		zone = Zone((16, 16), None)
		self.world.add_zone(zone_pos, zone)
		for pos in zone.fields:
			zone.fields.set_cell(pos, generate_field())

			shift = Point(
					pos.x * zone.field_size.width,
					pos.y * zone.field_size.height,
					)
			if random.randrange(50) == 0:
				add_building(zone.fields.cell(pos))
				continue
			monster_count = random.randrange(5) if random.randrange(5) == 0 else 0
			for _ in range(monster_count):
				monster_pos = Point(
						random.randrange(zone.fields.cell(pos).tiles.size.width),
						random.randrange(zone.fields.cell(pos).tiles.size.height),
						)
				while any(other.pos == monster_pos for other in zone.fields.cell(pos).monsters):
					monster_pos = Point(
							random.randrange(zone.fields.cell(pos).tiles.size.width),
							random.randrange(zone.fields.cell(pos).tiles.size.height),
							)
				colors = set(COLORS.keys()) - {'black'}
				normal_colors = [color for color in colors if not color.startswith('bold_')]
				bold_colors = [color for color in colors if color.startswith('bold_')]
				strong = random.randrange(2)
				aggressive = random.randrange(2)
				monster_color = random.choice(bold_colors if aggressive else normal_colors)
				monster = Monster(
					monster_pos,
					Sprite(
						random.choice(string.ascii_uppercase if strong else string.ascii_lowercase),
						monster_color,
						),
					1 + 10 * strong + random.randrange(4),
					behaviour='aggressive' if aggressive else None,
					)
				if random.randrange(2):
					monster.inventory.append(Item(
						None, Sprite('*', monster_color),
						'{0} skin'.format(monster_color.replace('_', ' ')),
						))
				zone.fields.cell(pos).monsters.append(monster)
		self.player.pos.zone = Point(
				random.randrange(zone.fields.size.width),
				random.randrange(zone.fields.size.height),
				)
		self.player.pos.field = Point(
				random.randrange(zone.field_size.width),
				random.randrange(zone.field_size.width),
				)

class Savefile:
	def __init__(self, filename, version):
		self.filename = filename
		self.version = version
	def exists(self):
		return self.filename.exists()
	def delete(self):
		if self.filename.exists():
			self.filename.unlink()

class SavefileReader:
	CHUNK_SIZE = 4096
	def __init__(self, savefile):
		self.savefile = savefile
		self.f = None
		self.buffer = ''
	def __enter__(self):
		self.f = open(self.savefile.filename, 'r')
		version = self.read(int)
		assert version == self.savefile.version, (version, self.savefile.version)
		return self
	def read(self, data_type=None):
		if not self.buffer:
			self.buffer = self.f.read(self.CHUNK_SIZE)
			assert self.buffer
		data = None
		while True:
			try:
				data, self.buffer = self.buffer.split('\0', 1)
				break
			except ValueError:
				new_chunk = self.f.read(self.CHUNK_SIZE)
				if not new_chunk:
					data = self.buffer
					break
				self.buffer += new_chunk
		if data_type:
			data = data_type(data)
		return data
	def __exit__(self, *_):
		self.f.close()

class SavefileWriter:
	def __init__(self, savefile):
		self.savefile = savefile
		self.f = None
	def __enter__(self):
		self.f = open(self.savefile.filename, 'w')
		self.f.write(str(self.savefile.version))
		return self
	def write(self, data):
		self.f.write('\0')
		self.f.write(str(data))
	def __exit__(self, *_):
		self.f.close()

def iter_rect(topleft, bottomright):
	for x in range(topleft.x, bottomright.x + 1):
		for y in range(topleft.y, bottomright.y + 1):
			yield Point(x, y)

def display_inventory(window, inventory, caption=None, select=False):
	window.clear()
	while True:
		if caption:
			window.addstr(0, 0, caption)
		accumulated = []
		for shortcut, item in zip(string.ascii_lowercase, inventory):
			for other in accumulated:
				if other[1].name == item.name:
					other[2] += 1
					break
			else:
				accumulated.append([shortcut, item, 1])
		for index, (shortcut, item, amount) in enumerate(accumulated):
			column = index // 20
			index = index % 20
			window.addstr(index + 1, column * 40 + 0, '[{0}] '.format(shortcut))
			window.addstr(index + 1, column * 40 + 4, item.sprite.sprite, COLORS[item.sprite.color])
			if amount > 1:
				window.addstr(index + 1, column * 40 + 6, '- {0} (x{1})'.format(item.name, amount))
			else:
				window.addstr(index + 1, column * 40 + 6, '- {0}'.format(item.name))
		control = window.getch()
		if control == curses.ascii.ESC:
			break
		if select:
			selected = control - ord('a')
			if selected < 0 or len(inventory) <= selected:
				caption = 'No such item: {0}'.format(chr(control))
			else:
				return selected
	return None

def main(window):
	curses.curs_set(0)
	init_colors()

	game = Game()
	savefile = Savefile(xdg.save_data_path('dotrogue')/'rogue.sav', 3)
	if savefile.exists():
		with SavefileReader(savefile) as reader:
			game.load(reader)
	else:
		game.generate()

	viewport = Rect((0, 0), (61, 23))
	center = Point(*(viewport.size // 2))
	centered_viewport = Rect((-center.x, -center.y), viewport.size)
	messages = []
	while True:
		full_zone_size = Size(
				game.world.zone_size.width * game.world.field_size.width,
				game.world.zone_size.height * game.world.field_size.height,
				)
		player_pos = game.player.pos.get_global(game.world)
		player_relative_pos = player_pos - center
		viewport_topleft = Coord.from_global(player_pos + centered_viewport.topleft, game.world)
		viewport_bottomright = Coord.from_global(player_pos + centered_viewport.bottomright, game.world)

		for zone_index in iter_rect(viewport_topleft.world, viewport_bottomright.world):
			zone = game.world.zones.cell(zone_index)
			if zone is None:
				continue
			zone_shift = Point(
						zone_index.x * full_zone_size.width,
						zone_index.y * full_zone_size.height,
						)
			for field_index in zone.fields:
				field = zone.fields.cell(field_index)
				field_size = field.tiles.size
				field_rect = Rect(zone_shift + Point(
							field_index.x * field_size.width,
							field_index.y * field_size.height,
							), field_size)
				control_points = [
						Point(field_rect.left, field_rect.top),
						Point(field_rect.right, field_rect.top),
						Point(field_rect.left, field_rect.bottom),
						Point(field_rect.right, field_rect.bottom),
						]
				if not any(viewport.contains(pos - player_relative_pos, with_border=True) for pos in control_points):
					continue
				field_topleft = field_rect.topleft - player_relative_pos
				for pos in field.tiles:
					screen_pos = pos + field_topleft
					if not viewport.contains(screen_pos, with_border=True):
						continue
					tile_sprite = field.tiles.cell(pos).sprite
					window.addstr(screen_pos.y, screen_pos.x, tile_sprite.sprite, COLORS[tile_sprite.color])
				for item in field.items:
					screen_pos = item.pos + field_topleft
					if not viewport.contains(screen_pos, with_border=True):
						continue
					window.addstr(screen_pos.y, screen_pos.x, item.sprite.sprite, COLORS[item.sprite.color])
				for monster in field.monsters:
					screen_pos = monster.pos + field_topleft
					if not viewport.contains(screen_pos, with_border=True):
						continue
					window.addstr(screen_pos.y, screen_pos.x, monster.sprite.sprite, COLORS[monster.sprite.color])
		window.addstr(center.y, center.x, game.player.sprite.sprite, COLORS[game.player.sprite.color])

		hud_pos = viewport.right + 1
		for row in range(5):
			window.addstr(row, hud_pos, " " * (80 - hud_pos))
		window.addstr(0, hud_pos, "@{0}".format(game.player.pos))
		window.addstr(1, hud_pos, "T:{0}".format(game.passed_time))
		window.addstr(2, hud_pos, "hp:{0}/{1}".format(game.player.hp, game.player.max_hp))
		window.addstr(3, hud_pos, "inv:{0}".format(len(game.player.inventory)))
		player_zone_items = game.world.zones.cell(game.player.pos.world).fields.cell(game.player.pos.zone).items
		item_here = next((
			item for item in player_zone_items
			if game.player.pos.field == item.pos
			), None)
		if item_here:
			window.addstr(4, hud_pos, "here:{0}".format(item.sprite.sprite))

		window.addstr(24, 0, " " * 80)
		while messages:
			message = messages.pop(0)
			if len(message) >= 80 - 5:
				message, tail = message[:80-5], message[80-5:]
				messages.insert(0, tail)
			else:
				while messages and len(message) + 1 + len(messages[0]) < 80 - 5:
					message += ' ' + messages.pop(0)
			message_line = message
			if messages:
				message_line += '[...]'
			window.addstr(24, 0, " " * 80)
			window.addstr(24, 0, message_line)
			if messages or game.player.hp <= 0:
				window.getch()

		if game.player.hp <= 0:
			break

		control = window.getch()
		step_taken = False
		player_pos = game.player.pos.get_global(game.world)
		if control == ord('S'):
			break
		elif control == ord('.'):
			step_taken = True
		elif control == ord('g'):
			item = next((
				item for item in
				game.world.zones.cell(game.player.pos.world).fields.cell(game.player.pos.zone).items
				if game.player.pos.field == item.pos
				), None)
			if not item:
				messages.append('Nothing to pick up here.')
			elif len(game.player.inventory) >= 26:
				messages.append('Inventory is full.')
			else:
				game.player.inventory.append(item)
				game.world.zones.cell(game.player.pos.world).fields.cell(game.player.pos.zone).items.remove(item)
				messages.append('Picked up {0}.'.format(item.name))
				step_taken = True
		elif control == ord('C'):
			npcs = [
					monster for monster_pos, monster
					in game.world.all_monsters()
					if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1
					and isinstance(monster.behaviour, Questgiver)
					]
			questing = [
					npc for _, npc in game.world.all_monsters()
					if isinstance(npc.behaviour, Questgiver)
					and npc.behaviour.quest
					]
			if not npcs:
				messages.append('No one to chat with.')
			elif len(questing) > 20:
				messages.append("Too much quests already.")
			else:
				if len(npcs) > 1:
					window.addstr(24, 0, " " * 80)
					window.addstr(24, 0, "Too crowded. Chat in which direction?")
					control = window.getch()
					if chr(control) in MOVEMENT:
						dest = player_pos + MOVEMENT[chr(control)]
						npcs = [npc for npc in npcs if npc.pos == dest]
					else:
						npcs = []
				if npcs:
					npc = npcs[0]
					if npc.behaviour.quest:
						required_amount, required_name, bounty = npc.behaviour.quest
						have_required_items = [
								item for item in game.player.inventory
								if item.name == required_name
								][:required_amount]
						if len(have_required_items) >= required_amount:
							window.addstr(24, 0, " " * 80)
							window.addstr(24, 0, '"You have {0} {1}. Trade it for +{2} max hp?" (y/n)'.format(*(npc.behaviour.quest)))
							control = window.getch()
							if chr(control) in 'yY':
								messages.append('"Thanks. Here you go."')
								for item in have_required_items:
									game.player.inventory.remove(item)
								if game.player.hp == game.player.max_hp:
									game.player.hp += bounty
								game.player.max_hp += bounty
								npc.behaviour.quest = None
							else:
								messages.append('"OK, come back later if you want it."')
						else:
							messages.append('"Come back with {0} {1}."'.format(*(npc.behaviour.quest)))
					else:
						if not npc.behaviour.prepared_quest:
							amount = 1 + random.randrange(3)
							bounty = max(1, amount // 2 + 1)
							color = random.choice(list(set(COLORS.keys()) - {'black'})).replace('_', ' ') + ' skin'
							npc.behaviour.prepared_quest = (amount, color, bounty)
						window.addstr(24, 0, " " * 80)
						window.addstr(24, 0, '"Bring me {0} {1}, trade it for +{2} max hp, deal?" (y/n)'.format(*(npc.behaviour.prepared_quest)))
						control = window.getch()
						if chr(control) in 'yY':
							npc.behaviour.quest = npc.behaviour.prepared_quest
							npc.behaviour.prepared_quest = None
						else:
							messages.append('"OK, come back later if you want it."')
				else:
					messages.append('No one to chat with in that direction.')
		elif control == ord('q'):
			window.clear()
			questing = [
					(coord, npc) for coord, npc in game.world.all_monsters(raw=True)
					if isinstance(npc.behaviour, Questgiver)
					and npc.behaviour.quest
					]
			if not questing:
				window.addstr(0, 0, "No current quests.")
			else:
				window.addstr(0, 0, "Current quests:")
			while True:
				for index, (coord, npc) in enumerate(questing):
					window.addstr(index + 1, 0, "@ {2}: Bring {0} {1}.".format(
						npc.behaviour.quest[0],
						npc.behaviour.quest[1],
						coord,
						))
				control = window.getch()
				if control == curses.ascii.ESC:
					break
		elif control == ord('i'):
			display_inventory(window, game.player.inventory)
		elif control == ord('d'):
			if not game.player.inventory:
				messages.append('Nothing to drop.')
			else:
				selected = display_inventory(window, game.player.inventory,
							 caption="Select item to drop (a-z/ESC):",
							 select=True
							 )
				if selected:
					item = game.player.inventory.pop(selected)
					item.pos = game.player.pos.field
					game.world.zones.cell(game.player.pos.world).fields.cell(game.player.pos.zone).items.append(item)
					messages.append('You drop {0}.'.format(item.name))
					step_taken = True
		elif chr(control) in MOVEMENT:
			new_pos = player_pos + MOVEMENT[chr(control)]
			dest_pos = Coord.from_global(new_pos, game.world)
			dest_field = None
			dest_cell = None
			if game.world.zones.valid(dest_pos.world):
				if game.world.zones.cell(dest_pos.world).fields.valid(dest_pos.zone):
					dest_field = game.world.zones.cell(dest_pos.world).fields.cell(dest_pos.zone)
					if dest_field.tiles.valid(dest_pos.field):
						dest_cell = dest_field.tiles.cell(dest_pos.field)
			monster = next((monster for monster in dest_field.monsters if dest_pos.field == monster.pos), None)
			if monster:
				if isinstance(monster.behaviour, Questgiver):
					messages.append('You bump into dweller.')
				else:
					monster.hp -= 1
					messages.append('You hit monster.')
					if monster.hp <= 0:
						dest_field.monsters.remove(monster)
						messages.append('Monster is dead.')
						for item in monster.inventory:
							item.pos = monster.pos
							monster.inventory.remove(item)
							dest_field.items.append(item)
							messages.append('Monster dropped {0}.'.format(item.name))
			elif dest_cell is None:
				messages.append('Will not fall into the void.')
			elif dest_cell.passable:
				game.player.pos = dest_pos
				game.autoexpand(game.player.pos, Size(40, 40))
			step_taken = True
		if step_taken:
			player_pos = game.player.pos.get_global(game.world)
			if game.player.hp < game.player.max_hp:
				game.player.regeneration += 1
				while game.player.regeneration >= 10:
					game.player.regeneration -= 10
					game.player.hp += 1
					if game.player.hp >= game.player.max_hp:
						game.player.hp = game.player.max_hp

			game.passed_time += 1

			monster_action_length = 10
			monster_action_range = Point(monster_action_length, monster_action_length)
			monster_zone_topleft = Coord.from_global(player_pos - monster_action_range, game.world)
			monster_zone_bottomright = Coord.from_global(player_pos + monster_action_range, game.world)
			monster_zone_range = iter_rect(monster_zone_topleft.world, monster_zone_bottomright.world)
			for monster_coord, monster in game.world.all_monsters(raw=True, zone_range=monster_zone_range):
				if isinstance(monster.behaviour, Questgiver):
					continue
				monster_pos = monster_coord.get_global(game.world)
				if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1:
					game.player.hp -= 1
					messages.append('Monster hits you.')
					if game.player.hp <= 0:
						messages.append('You died!!!')
				elif monster.behaviour == 'aggressive' and math.hypot(monster_pos.x - player_pos.x, monster_pos.y - player_pos.y) <= monster_action_length:
					shift = Point(
							sign(player_pos.x - monster_pos.x),
							sign(player_pos.y - monster_pos.y),
							)
					new_pos = monster_pos + shift
					dest_pos = Coord.from_global(new_pos, game.world)
					dest_field = game.world.zones.cell(dest_pos.world).fields.cell(dest_pos.zone)
					dest_cell = dest_field.tiles.cell(dest_pos.field)
					if any(other.pos == dest_pos.field for other in dest_field.monsters):
						messages.append('Monster bump into monster.')
					elif dest_cell.passable:
						if monster_coord.world != dest_pos.world or monster_coord.zone != dest_pos.zone:
							game.world.zones.cell(monster_coord.world).fields.cell(monster_coord.zone).monsters.remove(monster)
							dest_field.monsters.append(monster)
						monster.pos = dest_pos.field
	if game.player.hp > 0:
		with SavefileWriter(savefile) as writer:
			game.save(writer)
	else:
		savefile.delete()

curses.wrapper(main)
