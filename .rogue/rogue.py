import sys
import functools
import random
import math
import string
import logging
from collections import namedtuple
import curses
import clckwrkbdgr.logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Rect, Size, Matrix, sign
from clckwrkbdgr.math.grid import NestedGrid
from clckwrkbdgr import xdg
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.tui
from src.engine import builders

SAVEFILE_VERSION = 3

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

class Terrain:
	def __init__(self, sprite=None, passable=True):
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
		if isinstance(self.pos, NestedGrid.Coord):
			stream.write('|'.join(
				map(lambda p:','.join(map(str, p)), self.pos.values)
				))
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
			parts = (Point(*(map(int, part.split(',')))) for part in parts)
			self.pos = NestedGrid.Coord(*parts)
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

class ZoneData:
	def save(self, stream):
		pass
	@classmethod
	def load(cls, stream):
		return cls()

class FieldData:
	def __init__(self):
		self.items = []
		self.monsters = []
	def save(self, stream):
		stream.write(len(self.items))
		for item in self.items:
			item.save(stream)

		stream.write(len(self.monsters))
		for monster in self.monsters:
			monster.save(stream)
	@classmethod
	def load(cls, stream):
		self = cls()
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
		return self

class Builder(builders.Builder):
	class Mapping:
		bog = Terrain(Sprite('~', 'green'))
		bush = Terrain(Sprite('"', 'bold_green'))
		dead_tree = Terrain(Sprite('&', 'yellow'))
		frozen_ground = Terrain(Sprite('.', 'white'))
		grass = Terrain(Sprite('.', 'green'))
		ice = Terrain(Sprite('.', 'cyan'))
		plant = Terrain(Sprite('"', 'green'))
		rock = Terrain(Sprite('^', 'yellow'), passable=False)
		sand = Terrain(Sprite('.', 'bold_yellow'))
		snow = Terrain(Sprite('.', 'bold_white'))
		swamp = Terrain(Sprite('~', 'cyan'))
		tree = Terrain(Sprite('&', 'bold_green'))
		swamp_tree = Terrain(Sprite('&', 'green'))
		floor = Terrain(Sprite('.', 'white'))
		wall = Terrain(Sprite('#', 'white'), passable=False)
		def dweller(pos, color):
			return Monster(pos, Sprite('@', color), 10, behaviour=Questgiver())
		@classmethod
		def monster(cls, pos, sprite, color, strong, aggressive):
			return Monster(pos,
				Sprite(sprite.upper() if strong else sprite, color),
				1 + 10 * strong + random.randrange(4),
				behaviour='aggressive' if aggressive else None,
				)
		@classmethod
		def monster_carrying(cls, pos, sprite, color, strong, aggressive):
			result = cls.monster(pos, sprite, color, strong, aggressive)
			result.inventory.append(Item(
				None, Sprite('*', color),
				'{0} skin'.format(color.replace('_', ' ')),
				))
			return result

	def fill_grid(self, grid):
		self._make_terrain(grid)
		self._building = random.randrange(50) == 0
		if self._building:
			self._building = self._add_building(grid)
	def _add_building(self, grid):
		building = Rect(
				Point(2 + random.randrange(3), 2 + random.randrange(3)),
				Size(6 + random.randrange(3), 6 + random.randrange(3)),
				)
		for x in range(building.width):
			for y in range(building.height):
				grid.set_cell((building.left + x, building.top + y), 'floor')
		for x in range(building.width):
			grid.set_cell((building.left + x, building.top), 'wall')
			grid.set_cell((building.left + x, building.bottom), 'wall')
		for y in range(building.height):
			grid.set_cell((building.left, building.top + y), 'wall')
			grid.set_cell((building.right, building.top + y), 'wall')
		if random.randrange(2) == 0:
			door = building.top + 1 + random.randrange(building.height - 2)
			if random.randrange(2) == 0:
				grid.set_cell((building.left, door), 'floor')
			else:
				grid.set_cell((building.right, door), 'floor')
		else:
			door = building.left + 1 + random.randrange(building.width - 2)
			if random.randrange(2) == 0:
				grid.set_cell((door, building.top), 'floor')
			else:
				grid.set_cell((door, building.bottom), 'floor')
		return building
	def generate_actors(self, grid):
		if self._building:
			yield self._make_dweller(self._building)
			return
		monster_count = random.randrange(5) if random.randrange(5) == 0 else 0
		for _ in range(monster_count):
			yield self._make_monster(grid)
	def _make_dweller(self, building):
		dweller_pos = building.topleft + Point(1, 1) + Point(
				random.randrange(building.width - 2),
				random.randrange(building.height - 2),
				)
		colors = [name for name, color in Game.COLORS.items() if color.dweller]
		monster_color = random.choice(colors)
		return dweller_pos, 'dweller', monster_color
	def _make_monster(self, grid):
		monster_pos = Point(
				random.randrange(grid.size.width),
				random.randrange(grid.size.height),
				)
		while self.has_actor(monster_pos):
			monster_pos = Point(
					random.randrange(grid.size.width),
					random.randrange(grid.size.height),
					)
		colors = [name for name, color in Game.COLORS.items() if color.monster]
		normal_colors = [color for color in colors if not color.startswith('bold_')]
		bold_colors = [color for color in colors if color.startswith('bold_')]
		strong = random.randrange(2)
		aggressive = random.randrange(2)
		monster_color = random.choice(bold_colors if aggressive else normal_colors)
		key = 'monster_carrying' if random.randrange(2) else 'monster'
		return (
				monster_pos, key, 
				random.choice(string.ascii_lowercase),
				monster_color, strong, aggressive,
				)

class Forest(Builder):
	def _make_terrain(self, grid):
		grid.clear('grass')
		forest_density = random.randrange(10) * 10
		for _ in range(forest_density):
			grid.set_cell(self.point(), 'tree')
		for _ in range(10):
			grid.set_cell(self.point(), 'bush')
		for _ in range(10):
			grid.set_cell(self.point(), 'plant')

class Desert(Builder):
	def _make_terrain(self, grid):
		grid.clear('sand')
		for _ in range(random.randrange(3)):
			grid.set_cell(self.point(), 'rock')
		for _ in range(10):
			grid.set_cell(self.point(), 'plant')

class Thundra(Builder):
	def _make_terrain(self, grid):
		grid.clear('snow')
		for _ in range(3 + random.randrange(3)):
			grid.set_cell(self.point(), 'ice')
		for _ in range(3 + random.randrange(7)):
			grid.set_cell(self.point(), 'frozen_ground')

class Marsh(Builder):
	def _make_terrain(self, grid):
		grid.clear('swamp')
		for _ in range(100):
			grid.set_cell(self.point(), 'bog')
		for _ in range(random.randrange(100)):
			grid.set_cell(self.point(), 'grass')
		for _ in range(random.randrange(5)):
			grid.set_cell(self.point(), 'swamp_tree')
		for _ in range(random.randrange(10)):
			grid.set_cell(self.point(), 'dead_tree')

def all_monsters(world, raw=False, zone_range=None):
	for zone_index in (zone_range or world.cells):
		zone = world.cells.cell(zone_index)
		if zone is None:
			continue
		for field_index in zone.cells:
			for monster in zone.cells.cell(field_index).data.monsters:
				coord = NestedGrid.Coord(zone_index, field_index, monster.pos)
				if not raw:
					coord = coord.get_global(world)
				yield coord, monster

Color = namedtuple('Color', 'fg attr dweller monster')
class Game:
	COLORS = {
			'black': Color(curses.COLOR_BLACK, 0, False, False),
			'red': Color(curses.COLOR_RED, 0, True, True),
			'green': Color(curses.COLOR_GREEN, 0, True, True),
			'blue': Color(curses.COLOR_BLUE, 0, True, True),
			'yellow': Color(curses.COLOR_YELLOW, 0, True, True),
			'cyan': Color(curses.COLOR_CYAN, 0, True, True),
			'magenta': Color(curses.COLOR_MAGENTA, 0, True, True),
			'white': Color(curses.COLOR_WHITE, 0, True, True),
			'bold_black': Color(curses.COLOR_BLACK, curses.A_BOLD, True, True),
			'bold_red': Color(curses.COLOR_RED, curses.A_BOLD, True, True),
			'bold_green': Color(curses.COLOR_GREEN, curses.A_BOLD, True, True),
			'bold_blue': Color(curses.COLOR_BLUE, curses.A_BOLD, True, True),
			'bold_yellow': Color(curses.COLOR_YELLOW, curses.A_BOLD, True, True),
			'bold_cyan': Color(curses.COLOR_CYAN, curses.A_BOLD, True, True),
			'bold_magenta': Color(curses.COLOR_MAGENTA, curses.A_BOLD, True, True),
			'bold_white': Color(curses.COLOR_WHITE, curses.A_BOLD, False, True),
			}
	def __init__(self):
		self.player = Monster(NestedGrid.Coord(Point(0, 0), Point(0, 0), Point(0, 0)), Sprite('@', 'bold_white'), 10)
		self.world = NestedGrid([(256, 256), (16, 16), (16, 16)], [None, ZoneData, FieldData], Terrain)
		self.passed_time = 0
		self.colors = {}
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
				random.randrange(self.world.cells.size.width),
				random.randrange(self.world.cells.size.height),
				)
		zone = self.generate_zone(zone_pos)
		self.player.pos = NestedGrid.Coord(
				zone_pos,
				Point(
					random.randrange(zone.cells.size.width),
					random.randrange(zone.cells.size.height),
					),
				Point(
					random.randrange(zone.sizes[-1].width),
					random.randrange(zone.sizes[-1].width),
					),
				)
	def autoexpand(self, coord, margin):
		pos = coord.get_global(self.world)
		within_zone = Point(
				pos.x % (self.world.sizes[-2].width * self.world.sizes[-1].width),
				pos.y % (self.world.sizes[-2].height * self.world.sizes[-1].height),
				)
		close_to_zone_boundaries = False
		in_world_pos = coord.values[0]
		expansion = Point(0, 0)
		if within_zone.x - 40 < 0:
			close_to_zone_boundaries = True
			expansion.x = -1
		if within_zone.x + 40 >= self.world.cells.cell(in_world_pos).full_size.width:
			close_to_zone_boundaries = True
			expansion.x = +1
		if within_zone.y - 40 < 0:
			close_to_zone_boundaries = True
			expansion.y = -1
		if within_zone.y + 40 >= self.world.cells.cell(in_world_pos).full_size.height:
			close_to_zone_boundaries = True
			expansion.y = +1
		if not close_to_zone_boundaries:
			return
		if expansion.x:
			new_pos = in_world_pos + Point(expansion.x, 0)
			if self.world.cells.valid(new_pos) and self.world.cells.cell(new_pos) is None:
				self.generate_zone(new_pos)
		if expansion.y:
			new_pos = in_world_pos + Point(0, expansion.y)
			if self.world.cells.valid(new_pos) and self.world.cells.cell(new_pos) is None:
				self.generate_zone(new_pos)
		if expansion.x * expansion.y:
			new_pos = in_world_pos + expansion
			if self.world.cells.valid(new_pos) and self.world.cells.cell(new_pos) is None:
				self.generate_zone(new_pos)
	def generate_zone(self, zone_pos):
		zone = self.world.make_subgrid(zone_pos)
		for pos in zone.cells:
			field = zone.make_subgrid(pos)
			builder_type = random.choice([
				Forest,
				Desert,
				Thundra,
				Marsh,
				])
			builder = builder_type(random, field.cells)
			builder.generate()
			builder.make_grid()
			field.data.monsters.extend(builder.make_actors())
		return zone

def iter_rect(topleft, bottomright):
	for x in range(topleft.x, bottomright.x + 1):
		for y in range(topleft.y, bottomright.y + 1):
			yield Point(x, y)

InventoryKeys = clckwrkbdgr.tui.Keymapping()
InventoryKeys.map(list('abcdefghijlkmnopqrstuvwxyz'), lambda key:str(key))
InventoryKeys.map(clckwrkbdgr.tui.Key.ESCAPE, 'cancel')
class InventoryMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = False
	KEYMAPPING = InventoryKeys
	def __init__(self, inventory, caption=None, on_select=None):
		self.inventory = inventory
		self.caption = caption
		self.on_select = on_select
	def redraw(self, ui):
		if True:
			if self.caption:
				ui.print_line(0, 0, self.caption)
			accumulated = []
			for shortcut, item in zip(string.ascii_lowercase, self.inventory):
				for other in accumulated:
					if other[1].name == item.name:
						other[2] += 1
						break
				else:
					accumulated.append([shortcut, item, 1])
			for index, (shortcut, item, amount) in enumerate(accumulated):
				column = index // 20
				index = index % 20
				ui.print_line(index + 1, column * 40 + 0, '[{0}] '.format(shortcut))
				ui.print_line(index + 1, column * 40 + 4, item.sprite.sprite, item.sprite.color)
				if amount > 1:
					ui.print_line(index + 1, column * 40 + 6, '- {0} (x{1})'.format(item.name, amount))
				else:
					ui.print_line(index + 1, column * 40 + 6, '- {0}'.format(item.name))
	def action(self, control):
		if control == 'cancel':
			return None
		if self.on_select:
			selected = ord(control) - ord('a')
			if selected < 0 or len(self.inventory) <= selected:
				self.caption = 'No such item: {0}'.format(control)
			else:
				self.on_select(selected)
				return None
		return True

DialogKeys = clckwrkbdgr.tui.Keymapping()
DialogKeys.map(list('yY'), True)

QuestLogKeys = clckwrkbdgr.tui.Keymapping()
QuestLogKeys.map(clckwrkbdgr.tui.Key.ESCAPE, 'cancel')

def main(ui):
	debug = '--debug' in sys.argv
	if debug:
		clckwrkbdgr.logging.init(
			'rogue', debug=True, filename='rogue.log', stream=None,
			)

	for name, color in Game.COLORS.items():
		ui.init_color(name, color.fg, color.attr)

	game = Game()
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'rogue.sav')
	with savefile.get_reader() as reader:
		if reader:
			assert reader.version == SAVEFILE_VERSION, (reader.version, SAVEFILE_VERSION)
			game.load(reader)
		else:
			game.generate()

	main_game = MainGameMode(game)
	loop = clckwrkbdgr.tui.ModeLoop(ui)
	loop.run(main_game)
	if game.player.hp > 0:
		with savefile.save(SAVEFILE_VERSION) as writer:
			game.save(writer)
	else:
		savefile.unlink()

Keys = clckwrkbdgr.tui.Keymapping()
class MainGameMode(clckwrkbdgr.tui.Mode):
	KEYMAPPING = Keys
	def __init__(self, game):
		self.game = game
		self.viewport = Rect((0, 0), (61, 23))
		self.center = Point(*(self.viewport.size // 2))
		self.centered_viewport = Rect((-self.center.x, -self.center.y), self.viewport.size)
		self.messages = []
	def redraw(self, ui):
		game = self.game
		full_zone_size = Size(
				game.world.sizes[-2].width * game.world.sizes[-1].width,
				game.world.sizes[-2].height * game.world.sizes[-1].height,
				)
		player_pos = game.player.pos.get_global(game.world)
		player_relative_pos = player_pos - self.center
		viewport_topleft = NestedGrid.Coord.from_global(player_pos + self.centered_viewport.topleft, game.world)
		viewport_bottomright = NestedGrid.Coord.from_global(player_pos + self.centered_viewport.bottomright, game.world)

		for zone_index in iter_rect(viewport_topleft.values[0], viewport_bottomright.values[0]):
			zone = game.world.cells.cell(zone_index)
			if zone is None:
				continue
			zone_shift = Point(
						zone_index.x * full_zone_size.width,
						zone_index.y * full_zone_size.height,
						)
			for field_index in zone.cells:
				field = zone.cells.cell(field_index)
				field_rect = Rect(zone_shift + Point(
							field_index.x * field.full_size.width,
							field_index.y * field.full_size.height,
							), field.full_size)
				control_points = [
						Point(field_rect.left, field_rect.top),
						Point(field_rect.right, field_rect.top),
						Point(field_rect.left, field_rect.bottom),
						Point(field_rect.right, field_rect.bottom),
						]
				if not any(self.viewport.contains(pos - player_relative_pos, with_border=True) for pos in control_points):
					continue
				field_topleft = field_rect.topleft - player_relative_pos
				for pos in field.cells:
					screen_pos = pos + field_topleft
					if not self.viewport.contains(screen_pos, with_border=True):
						continue
					tile_sprite = field.cells.cell(pos).sprite
					ui.print_char(screen_pos.x, screen_pos.y, tile_sprite.sprite, tile_sprite.color)
				for item in field.data.items:
					screen_pos = item.pos + field_topleft
					if not self.viewport.contains(screen_pos, with_border=True):
						continue
					ui.print_char(screen_pos.x, screen_pos.y, item.sprite.sprite, item.sprite.color)
				for monster in field.data.monsters:
					screen_pos = monster.pos + field_topleft
					if not self.viewport.contains(screen_pos, with_border=True):
						continue
					ui.print_char(screen_pos.x, screen_pos.y, monster.sprite.sprite, monster.sprite.color)
		ui.print_char(self.center.x, self.center.y, game.player.sprite.sprite, game.player.sprite.color)

		hud_pos = self.viewport.right + 1
		for row in range(5):
			ui.print_line(row, hud_pos, " " * (80 - hud_pos))
		ui.print_line(0, hud_pos, "@{0:02X}.{1:X}.{2:X};{3:02X}.{4:X}.{5:X}".format(
			game.player.pos.values[0].x,
			game.player.pos.values[1].x,
			game.player.pos.values[2].x,
			game.player.pos.values[0].y,
			game.player.pos.values[1].y,
			game.player.pos.values[2].y,
			))
		ui.print_line(1, hud_pos, "T:{0}".format(game.passed_time))
		ui.print_line(2, hud_pos, "hp:{0}/{1}".format(game.player.hp, game.player.max_hp))
		ui.print_line(3, hud_pos, "inv:{0}".format(len(game.player.inventory)))
		player_zone_items = game.world.get_data(game.player.pos)[-1].items
		item_here = next((
			item for item in player_zone_items
			if game.player.pos.values[-1] == item.pos
			), None)
		if item_here:
			ui.print_line(4, hud_pos, "here:{0}".format(item.sprite.sprite))

		ui.print_line(24, 0, " " * 80)
		while self.messages:
			message = self.messages.pop(0)
			if len(message) >= 80 - 5:
				message, tail = message[:80-5], message[80-5:]
				self.messages.insert(0, tail)
			else:
				while self.messages and len(message) + 1 + len(self.messages[0]) < 80 - 5:
					message += ' ' + self.messages.pop(0)
			message_line = message
			if self.messages:
				message_line += '[...]'
			ui.print_line(24, 0, " " * 80)
			ui.print_line(24, 0, message_line)
			if self.messages or game.player.hp <= 0:
				ui.get_keypress()
	def pre_action(self):
		if self.game.player.hp <= 0:
			return False
		self.step_taken = False
		return True
	@Keys.bind('S')
	def exit_game(self):
		return 'quit'
	@Keys.bind('.')
	def wait(self):
		if True:
			self.step_taken = True
	@Keys.bind('g')
	def grab_item(self):
		game = self.game
		if True:
			item = next((
				item for item in
				game.world.get_data(game.player.pos)[-1].items
				if game.player.pos.values[-1] == item.pos
				), None)
			if not item:
				self.messages.append('Nothing to pick up here.')
			elif len(game.player.inventory) >= 26:
				self.messages.append('Inventory is full.')
			else:
				game.player.inventory.append(item)
				game.world.get_data(game.player.pos)[-1].items.remove(item)
				self.messages.append('Picked up {0}.'.format(item.name))
				self.step_taken = True
	@Keys.bind('C')
	def char(self):
		game = self.game
		player_pos = game.player.pos.get_global(game.world)
		if True:
			npcs = [
					monster for monster_pos, monster
					in all_monsters(game.world)
					if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1
					and isinstance(monster.behaviour, Questgiver)
					]
			questing = [
					npc for _, npc in all_monsters(game.world)
					if isinstance(npc.behaviour, Questgiver)
					and npc.behaviour.quest
					]
			if not npcs:
				self.messages.append('No one to chat with.')
			elif len(questing) > 20:
				self.messages.append("Too much quests already.")
			else:
				if len(npcs) > 1:
					def _on_direction(direction):
						dest = player_pos + dialog.answer
						npcs = [npc for npc in npcs if npc.pos == dest]
						return self._chat_with_npcs(npcs)
					return DirectionDialogMode(on_direction=_on_direction)
				return self._chat_with_npcs(npcs)
	def _chat_with_npcs(self, npcs):
		if True:
			if True:
				if npcs:
					npc = npcs[0]
					return self._chat_with_npc(npc)
				else:
					self.messages.append('No one to chat with in that direction.')
	def _chat_with_npc(self, npc):
		game = self.game
		if True:
			if True:
				if True:
					if npc.behaviour.quest:
						required_amount, required_name, bounty = npc.behaviour.quest
						have_required_items = [
								item for item in game.player.inventory
								if item.name == required_name
								][:required_amount]
						if len(have_required_items) >= required_amount:
							def _on_yes():
								self.messages.append('"Thanks. Here you go."')
								for item in have_required_items:
									game.player.inventory.remove(item)
								if game.player.hp == game.player.max_hp:
									game.player.hp += bounty
								game.player.max_hp += bounty
								npc.behaviour.quest = None
							def _on_no():
								self.messages.append('"OK, come back later if you want it."')
							return TradeDialogMode('"You have {0} {1}. Trade it for +{2} max hp?" (y/n)'.format(*(self.npc.behaviour.quest)),
										on_yes=_on_yes, on_no=_on_no)
						else:
							self.messages.append('"Come back with {0} {1}."'.format(*(npc.behaviour.quest)))
					else:
						if not npc.behaviour.prepared_quest:
							amount = 1 + random.randrange(3)
							bounty = max(1, amount // 2 + 1)
							colors = [name for name, color in game.COLORS.items() if color.monster]
							color = random.choice(colors).replace('_', ' ') + ' skin'
							npc.behaviour.prepared_quest = (amount, color, bounty)
						def _on_yes():
							npc.behaviour.quest = npc.behaviour.prepared_quest
							npc.behaviour.prepared_quest = None
						def _on_no():
							self.messages.append('"OK, come back later if you want it."')
						return TradeDialogMode('"Bring me {0} {1}, trade it for +{2} max hp, deal?" (y/n)'.format(*(npc.behaviour.prepared_quest)),
										 on_yes=_on_yes, on_no=_on_no)
	@Keys.bind('q')
	def show_questlog(self):
		game = self.game
		if True:
			questing = [
					(coord, npc) for coord, npc in all_monsters(game.world, raw=True)
					if isinstance(npc.behaviour, Questgiver)
					and npc.behaviour.quest
					]
			quest_log = QuestLog(questing)
			return quest_log
	@Keys.bind('i')
	def display_inventory(self):
		return InventoryMode(self.game.player.inventory)
	@Keys.bind('d')
	def drop_item(self):
		game = self.game
		if True:
			if not game.player.inventory:
				self.messages.append('Nothing to drop.')
			else:
				def _on_select_item(menu_choice):
					item = game.player.inventory.pop(menu_choice)
					item.pos = game.player.pos.values[-1]
					game.world.get_data(game.player.pos)[-1].items.append(item)
					self.messages.append('You drop {0}.'.format(item.name))
					self.step_taken = True
				return InventoryMode(
						game.player.inventory,
						caption="Select item to drop (a-z/ESC):",
						on_select=_on_select_item
					)
	@Keys.bind(list('hjklyubn'), lambda key:MOVEMENT[str(key)])
	def move_player(self, control):
		game = self.game
		player_pos = game.player.pos.get_global(game.world)
		if True:
			new_pos = player_pos + control
			dest_pos = NestedGrid.Coord.from_global(new_pos, game.world)
			dest_field_data = None
			dest_cell = None
			if game.world.valid(dest_pos):
				dest_field_data = game.world.get_data(dest_pos)[-1]
				dest_cell = game.world.cell(dest_pos)
			monster = next((monster for monster in dest_field_data.monsters if dest_pos.values[-1] == monster.pos), None)
			if monster:
				if isinstance(monster.behaviour, Questgiver):
					self.messages.append('You bump into dweller.')
				else:
					monster.hp -= 1
					self.messages.append('You hit monster.')
					if monster.hp <= 0:
						dest_field_data.monsters.remove(monster)
						self.messages.append('Monster is dead.')
						for item in monster.inventory:
							item.pos = monster.pos
							monster.inventory.remove(item)
							dest_field_data.items.append(item)
							self.messages.append('Monster dropped {0}.'.format(item.name))
			elif dest_cell is None:
				self.messages.append('Will not fall into the void.')
			elif dest_cell.passable:
				game.player.pos = dest_pos
				game.autoexpand(game.player.pos, Size(40, 40))
			self.step_taken = True
	def action(self, control):
		if control == 'quit':
			return False
		game = self.game
		if self.step_taken:
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
			monster_zone_topleft = NestedGrid.Coord.from_global(player_pos - monster_action_range, game.world)
			monster_zone_bottomright = NestedGrid.Coord.from_global(player_pos + monster_action_range, game.world)
			monster_zone_range = iter_rect(monster_zone_topleft.values[0], monster_zone_bottomright.values[0])
			already_acted_monsters_from_previous_fields = []
			for monster_coord, monster in all_monsters(game.world, raw=True, zone_range=monster_zone_range):
				if monster in already_acted_monsters_from_previous_fields:
					continue
				if isinstance(monster.behaviour, Questgiver):
					continue
				monster_pos = monster_coord.get_global(game.world)
				if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1:
					game.player.hp -= 1
					self.messages.append('Monster hits you.')
					if game.player.hp <= 0:
						self.messages.append('You died!!!')
				elif monster.behaviour == 'aggressive' and math.hypot(monster_pos.x - player_pos.x, monster_pos.y - player_pos.y) <= monster_action_length:
					shift = Point(
							sign(player_pos.x - monster_pos.x),
							sign(player_pos.y - monster_pos.y),
							)
					new_pos = monster_pos + shift
					dest_pos = NestedGrid.Coord.from_global(new_pos, game.world)
					dest_field_data = game.world.get_data(dest_pos)[-1]
					dest_cell = game.world.cell(dest_pos)
					if any(other.pos == dest_pos.values[-1] for other in dest_field_data.monsters):
						self.messages.append('Monster bump into monster.')
					elif dest_cell.passable:
						current_field_data = game.world.get_data(monster_coord)[-1]
						if current_field_data != dest_field_data:
							current_field_data.monsters.remove(monster)
							dest_field_data.monsters.append(monster)
							already_acted_monsters_from_previous_fields.append(monster)
						monster.pos = dest_pos.values[-1]
		return True

DirectionKeys = clckwrkbdgr.tui.Keymapping()
class DirectionDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DirectionKeys
	def __init__(self, on_direction=None):
		self.on_direction = on_direction
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, "Too crowded. Chat in which direction?")
	@DirectionKeys.bind(list('hjklyubn'), lambda key:MOVEMENT[str(key)])
	def choose_direction(self, direction):
		if self.on_direction:
			return self.on_direction(direction)
		return False
	def action(self, control):
		return False

class TradeDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DialogKeys
	def __init__(self, question, on_yes=None, on_no=None):
		self.question = question
		self.on_yes = on_yes
		self.on_no = on_no
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, self.question)
	def action(self, control):
		if control:
			if self.on_yes:
				self.on_yes()
		else:
			if self.on_no:
				self.on_no()

class QuestLog(clckwrkbdgr.tui.Mode):
	TRANSPARENT = False
	KEYMAPPING = QuestLogKeys
	def __init__(self, quests):
		self.quests = quests
	def redraw(self, ui):
		if not self.quests:
			ui.print_line(0, 0, "No current quests.")
		else:
			ui.print_line(0, 0, "Current quests:")
		for index, (coord, npc) in enumerate(self.quests):
			ui.print_line(index + 1, 0, "@ {2}: Bring {0} {1}.".format(
				npc.behaviour.quest[0],
				npc.behaviour.quest[1],
				coord,
				))
	def action(self, control):
		return control != 'cancel'

with clckwrkbdgr.tui.Curses() as ui:
	main(ui)
