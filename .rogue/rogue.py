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
	curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
	COLORS.update({
		'green' : curses.color_pair(curses.COLOR_GREEN),
		'bold_green' : curses.color_pair(curses.COLOR_GREEN) | curses.A_BOLD,
		'bold_white' : curses.color_pair(curses.COLOR_WHITE) | curses.A_BOLD,
		})

def generate_field():
	field = Matrix((16, 16), Sprite('.', 'green'))
	forest_density = random.randrange(10) * 10
	for _ in range(forest_density):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('T', 'bold_green'))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('"', 'bold_green'))
	for _ in range(10):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('"', 'green'))
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
				if new_pos.y < 0:
					player.y = new_pos.y + field.size.height
				elif new_pos.y >= field.size.height:
					player.y = new_pos.y - field.size.height

curses.wrapper(main)
