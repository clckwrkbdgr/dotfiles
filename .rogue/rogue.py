import random
import math
import string
from collections import namedtuple
import curses, curses.ascii
import jsonpickle
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

class Terrain:
	def __init__(self, sprite, passable=True):
		self.sprite = sprite
		self.passable = passable

class Questgiver:
	def __init__(self):
		self.quest = None
		self.prepared_quest = None

class Monster:
	def __init__(self, pos, sprite, max_hp, behaviour=None):
		self.pos = pos
		self.sprite = sprite
		self.hp = self.max_hp = max_hp
		self.regeneration = 0
		self.behaviour = behaviour
		self.inventory = []

class Item:
	def __init__(self, pos, sprite, name):
		self.pos = pos
		self.sprite = sprite
		self.name = name

def generate_field():
	return random.choice([
		generate_forest,
		generate_desert,
		generate_thundra,
		generate_marsh,
		])()

def generate_forest():
	field = Matrix((16, 16), Terrain(Sprite('.', 'green')))
	forest_density = random.randrange(10) * 10
	for _ in range(forest_density):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('&', 'bold_green')))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('"', 'bold_green')))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('"', 'green')))
	return field

def generate_desert():
	field = Matrix((16, 16), Terrain(Sprite('.', 'bold_yellow')))
	for _ in range(random.randrange(3)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('^', 'yellow'), passable=False))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('"', 'green')))
	return field

def generate_thundra():
	field = Matrix((16, 16), Terrain(Sprite('.', 'bold_white')))
	for _ in range(3 + random.randrange(3)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('.', 'cyan')))
	for _ in range(3 + random.randrange(7)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('.', 'white')))
	return field

def generate_marsh():
	field = Matrix((16, 16), Terrain(Sprite('~', 'cyan')))
	for _ in range(100):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('~', 'green')))
	for _ in range(random.randrange(100)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('.', 'green')))
	for _ in range(random.randrange(5)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('&', 'green')))
	for _ in range(random.randrange(10)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Terrain(Sprite('&', 'yellow')))
	return field

def add_building(field, field_shift):
	building = Rect(
			Point(2 + random.randrange(3), 2 + random.randrange(3)),
			Size(6 + random.randrange(3), 6 + random.randrange(3)),
			)
	for x in range(building.width):
		for y in range(building.height):
			field.set_cell((building.left + x, building.top + y), Terrain(Sprite('.', 'white')))
	for x in range(building.width):
		field.set_cell((building.left + x, building.top), Terrain(Sprite('#', 'white'), passable=False))
		field.set_cell((building.left + x, building.bottom), Terrain(Sprite('#', 'white'), passable=False))
	for y in range(building.height):
		field.set_cell((building.left, building.top + y), Terrain(Sprite('#', 'white'), passable=False))
		field.set_cell((building.right, building.top + y), Terrain(Sprite('#', 'white'), passable=False))
	if random.randrange(2) == 0:
		door = building.top + 1 + random.randrange(building.height - 2)
		if random.randrange(2) == 0:
			field.set_cell((building.left, door), Terrain(Sprite('.', 'white')))
		else:
			field.set_cell((building.right, door), Terrain(Sprite('.', 'white')))
	else:
		door = building.left + 1 + random.randrange(building.width - 2)
		if random.randrange(2) == 0:
			field.set_cell((door, building.top), Terrain(Sprite('.', 'white')))
		else:
			field.set_cell((door, building.bottom), Terrain(Sprite('.', 'white')))
	dweller_pos = field_shift + building.topleft + Point(1, 1) + Point(
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
	return dweller

class Game:
	def __init__(self):
		self.player = Monster(Point(0, 0), Sprite('@', 'bold_white'), 10)
		self.world = Matrix((16, 16), None) # TODO not a world, just a local zone. need a 256x256 overworld of fixed zones, and the overworld itself may expand instead of sub-zones.
		self.monsters = []
		self.items = []
		self.passed_time = 0
	def generate(self):
		for pos in self.world:
			self.world.set_cell(pos, generate_field())

			world_size = Size(
					self.world.size.width * self.world.cell((0, 0)).size.width,
					self.world.size.height * self.world.cell((0, 0)).size.height,
					)
			shift = Point(
					pos.x * self.world.cell((0, 0)).size.width,
					pos.y * self.world.cell((0, 0)).size.height,
					)
			if random.randrange(50) == 0:
				dweller = add_building(self.world.cell(pos), shift)
				self.monsters.append(dweller)
				continue
			monster_count = random.randrange(5) if random.randrange(5) == 0 else 0
			for _ in range(monster_count):
				monster_pos = shift + Point(
						random.randrange(self.world.cell(pos).size.width),
						random.randrange(self.world.cell(pos).size.height),
						)
				while any(other.pos == monster_pos for other in self.monsters):
					monster_pos = shift + Point(
							random.randrange(self.world.cell(pos).size.width),
							random.randrange(self.world.cell(pos).size.height),
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
				self.monsters.append(monster)
		self.player.pos = Point(
				80 + random.randrange(self.world.size.width * self.world.cell((0, 0)).size.width - 80 * 2),
				80 + random.randrange(self.world.size.width * self.world.cell((0, 0)).size.width - 80 * 2),
				)

def main(window):
	curses.curs_set(0)
	init_colors()

	game = Game()
	savefile = xdg.save_data_path('dotrogue')/'rogue.sav'
	if savefile.exists():
		data = savefile.read_text()
		savedata = jsonpickle.decode(data, keys=True)
		game = savedata['entity']
	else:
		game.generate()

	viewport = Rect((0, 0), (61, 23))
	center = Point(*(viewport.size // 2))
	messages = []
	while True:
		window.clear()
		for field_index in game.world:
			field = game.world.cell(field_index)
			field_size = field.size
			field_rect = Rect(Point(
						field_index.x * field_size.width,
						field_index.y * field_size.height,
						), field_size)
			control_points = [
					Point(field_rect.left, field_rect.top),
					Point(field_rect.right, field_rect.top),
					Point(field_rect.left, field_rect.bottom),
					Point(field_rect.right, field_rect.bottom),
					]
			screen_control_points = [(pos) - game.player.pos + center for pos in control_points]
			if not any(viewport.contains(screen_pos, with_border=True) for screen_pos in screen_control_points):
				continue
			for pos in field:
				screen_pos = pos + field_rect.topleft - game.player.pos + center
				if not viewport.contains(screen_pos, with_border=True):
					continue
				window.addstr(screen_pos.y, screen_pos.x, field.cell(pos).sprite.sprite, COLORS[field.cell(pos).sprite.color])
		for item in game.items:
			screen_pos = item.pos - game.player.pos + center
			if not viewport.contains(screen_pos, with_border=True):
				continue
			window.addstr(screen_pos.y, screen_pos.x, item.sprite.sprite, COLORS[item.sprite.color])
		for monster in game.monsters:
			screen_pos = monster.pos - game.player.pos + center
			if not viewport.contains(screen_pos, with_border=True):
				continue
			window.addstr(screen_pos.y, screen_pos.x, monster.sprite.sprite, COLORS[monster.sprite.color])
		window.addstr(center.y, center.x, game.player.sprite.sprite, COLORS[game.player.sprite.color])

		hud_pos = viewport.right + 1
		window.addstr(0, hud_pos, "@{0};{1}".format(game.player.pos.x, game.player.pos.y))
		window.addstr(1, hud_pos, "T:{0}".format(game.passed_time))
		window.addstr(2, hud_pos, "hp:{0}/{1}".format(game.player.hp, game.player.max_hp))
		window.addstr(3, hud_pos, "inv:{0}".format(len(game.player.inventory)))
		item_here = next((item for item in game.items if game.player.pos == item.pos), None)
		if item_here:
			window.addstr(4, hud_pos, "here:{0}".format(item.sprite.sprite))

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

		step_taken = False
		control = window.getch()
		if control == ord('S'):
			break
		elif control == ord('.'):
			step_taken = True
		elif control == ord('g'):
			item = next((item for item in game.items if game.player.pos == item.pos), None)
			if not item:
				messages.append('Nothing to pick up here.')
			elif len(game.player.inventory) >= 26:
				messages.append('Inventory is full.')
			else:
				game.player.inventory.append(item)
				game.items.remove(item)
				messages.append('Picked up {0}.'.format(item.name))
				step_taken = True
		elif control == ord('C'):
			npcs = [
					monster for monster in game.monsters
					if max(abs(monster.pos.x - game.player.pos.x), abs(monster.pos.y - game.player.pos.y)) <= 1
					and isinstance(monster.behaviour, Questgiver)
					]
			questing = [
					npc for npc in game.monsters
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
						dest = game.player.pos + MOVEMENT[chr(control)]
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
					npc for npc in game.monsters
					if isinstance(npc.behaviour, Questgiver)
					and npc.behaviour.quest
					]
			if not questing:
				window.addstr(0, 0, "No current quests.")
			else:
				window.addstr(0, 0, "Current quests:")
			while True:
				for index, npc in enumerate(questing):
					window.addstr(index + 1, 0, "@ {2}: Bring {0} {1}.".format(
						npc.behaviour.quest[0],
						npc.behaviour.quest[1],
						npc.pos,
						))
				control = window.getch()
				if control == curses.ascii.ESC:
					break
		elif control == ord('i'):
			window.clear()
			while True:
				for index, (shortcut, item) in enumerate(zip(string.ascii_lowercase, game.player.inventory)):
					column = index // 20
					index = index % 20
					window.addstr(index + 1, column * 40 + 0, item.sprite.sprite, COLORS[item.sprite.color])
					window.addstr(index + 1, column * 40 + 2, '- {0}'.format(item.name))
				control = window.getch()
				if control == curses.ascii.ESC:
					break
		elif control == ord('d'):
			if not game.player.inventory:
				messages.append('Nothing to drop.')
			else:
				window.clear()
				caption = "Select item to drop (a-z/ESC):"
				while True:
					window.addstr(0, 0, caption)
					for index, (shortcut, item) in enumerate(zip(string.ascii_lowercase, game.player.inventory)):
						column = index // 20
						index = index % 20
						window.addstr(index + 1, column * 40 + 0, item.sprite.sprite, COLORS[item.sprite.color])
						window.addstr(index + 1, column * 40 + 2, '- {0}'.format(item.name))
					control = window.getch()
					if control == curses.ascii.ESC:
						break
					selected = control - ord('a')
					if selected < 0 or len(game.player.inventory) <= selected:
						caption = 'No such item: {0}'.format(chr(control))
					else:
						item = game.player.inventory.pop(selected)
						item.pos = game.player.pos
						game.items.append(item)
						messages.append('You drop {0}.'.format(item.name))
						step_taken = True
						break
		elif chr(control) in MOVEMENT:
			new_pos = game.player.pos + MOVEMENT[chr(control)]
			monster = next((monster for monster in game.monsters if new_pos == monster.pos), None)
			dest_pos = new_pos
			try:
				dest_cell = game.world.cell(Point(
						dest_pos.x // game.world.cell((0, 0)).width,
						dest_pos.y // game.world.cell((0, 0)).height,
						)).cell(Point(
							dest_pos.x % game.world.cell((0, 0)).width,
							dest_pos.y % game.world.cell((0, 0)).height,
							))
			except: # TODO proper boundaries check.
				dest_cell = None
				pass
			if monster:
				if isinstance(monster.behaviour, Questgiver):
					messages.append('You bump into dweller.')
				else:
					monster.hp -= 1
					messages.append('You hit monster.')
					if monster.hp <= 0:
						game.monsters.remove(monster)
						messages.append('Monster is dead.')
						for item in monster.inventory:
							item.pos = monster.pos
							monster.inventory.remove(item)
							game.items.append(item)
							messages.append('Monster dropped {0}.'.format(item.name))
			elif dest_cell is None:
				messages.append('Will not fall into the void.')
			elif dest_cell.passable:
				game.player.pos = new_pos
			step_taken = True
		if step_taken:
			if game.player.hp < game.player.max_hp:
				game.player.regeneration += 1
				while game.player.regeneration >= 10:
					game.player.regeneration -= 10
					game.player.hp += 1
					if game.player.hp >= game.player.max_hp:
						game.player.hp = game.player.max_hp
			game.passed_time += 1
			for monster in game.monsters:
				if isinstance(monster.behaviour, Questgiver):
					continue
				if max(abs(monster.pos.x - game.player.pos.x), abs(monster.pos.y - game.player.pos.y)) <= 1:
					game.player.hp -= 1
					messages.append('Monster hits you.')
					if game.player.hp <= 0:
						messages.append('You died!!!')
				elif monster.behaviour == 'aggressive' and math.hypot(monster.pos.x - game.player.pos.x, monster.pos.y - game.player.pos.y) <= 10:
					shift = Point(
							sign(game.player.pos.x - monster.pos.x),
							sign(game.player.pos.y - monster.pos.y),
							)
					new_pos = monster.pos + shift
					dest_pos = new_pos
					dest_cell = game.world.cell(Point(
								dest_pos.x // game.world.cell((0, 0)).width,
								dest_pos.y // game.world.cell((0, 0)).height,
								)).cell(Point(
									dest_pos.x % game.world.cell((0, 0)).width,
									dest_pos.y % game.world.cell((0, 0)).height,
									))
					if any(other.pos == new_pos for other in game.monsters):
						messages.append('Monster bump into monster.')
					elif dest_cell.passable:
						monster.pos = new_pos
	if game.player.hp > 0:
		savedata = {'entity': game}
		data = jsonpickle.encode(savedata, keys=True)
		savefile.write_bytes(data.encode('utf-8', 'replace'))
	else:
		if savefile.exists():
			savefile.unlink()

curses.wrapper(main)
