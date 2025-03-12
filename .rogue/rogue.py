import random
from collections import namedtuple
import curses
from clckwrkbdgr.math import Point, Size, Matrix

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

def generate_field():
	return random.choice([
		generate_forest,
		generate_desert,
		generate_thundra,
		generate_marsh,
		])()

def generate_forest():
	field = Matrix((16, 16), Sprite('.', 'green'))
	forest_density = random.randrange(10) * 10
	for _ in range(forest_density):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('T', 'bold_green'))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('"', 'bold_green'))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('"', 'green'))
	return field

def generate_desert():
	field = Matrix((16, 16), Sprite('.', 'bold_yellow'))
	for _ in range(random.randrange(3)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('^', 'yellow'))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('"', 'green'))
	return field

def generate_thundra():
	field = Matrix((16, 16), Sprite('.', 'bold_white'))
	for _ in range(3 + random.randrange(3)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('.', 'cyan'))
	for _ in range(3 + random.randrange(7)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('.', 'white'))
	return field

def generate_marsh():
	field = Matrix((16, 16), Sprite('.', 'green'))
	for _ in range(100):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('~', 'green'))
	for _ in range(random.randrange(100)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('~', 'cyan'))
	for _ in range(random.randrange(5)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('T', 'green'))
	for _ in range(random.randrange(10)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('T', 'yellow'))
	return field

def main(window):
	player = Point(0, 0)
	field = generate_field()

	curses.curs_set(0)
	init_colors()
	while True:
		for pos in field:
			window.addstr(pos.y, pos.x, field.cell(pos).sprite, COLORS[field.cell(pos).color])
		window.addstr(player.y, player.x, '@', COLORS['bold_white'])

		control = window.getch()
		if control == ord('q'):
			break
		elif chr(control) in MOVEMENT:
			new_pos = player + MOVEMENT[chr(control)]
			if field.valid(new_pos):
				player = new_pos
			else:
				field = generate_field()
				if new_pos.x < 0:
					player.x = new_pos.x + field.size.width
				elif new_pos.x >= field.size.width:
					player.x = new_pos.x - field.size.width
				else:
					player.x = new_pos.x
				if new_pos.y < 0:
					player.y = new_pos.y + field.size.height
				elif new_pos.y >= field.size.height:
					player.y = new_pos.y - field.size.height
				else:
					player.y = new_pos.y

curses.wrapper(main)
