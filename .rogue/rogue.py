import random
from collections import namedtuple
import curses
from clckwrkbdgr.math import Point, Rect, Size, Matrix

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

class Monster:
	def __init__(self, pos, sprite, max_hp):
		self.pos = pos
		self.sprite = sprite
		self.hp = self.max_hp = max_hp

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
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('&', 'bold_green'))
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
	field = Matrix((16, 16), Sprite('~', 'cyan'))
	for _ in range(100):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('~', 'green'))
	for _ in range(random.randrange(100)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('.', 'green'))
	for _ in range(random.randrange(5)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('&', 'green'))
	for _ in range(random.randrange(10)):
		field.set_cell(Point(random.randrange(16), random.randrange(16)), Sprite('&', 'yellow'))
	return field

def main(window):
	player = Monster(Point(0, 0), Sprite('@', 'bold_white'), 10)
	world = Matrix((16, 16), None) # TODO not a world, just a local zone. need a 256x256 overworld of fixed zones, and the overworld itself may expand instead of sub-zones.
	for pos in world:
		world.set_cell(pos, generate_field())

	curses.curs_set(0)
	init_colors()
	viewport = Rect((0, 0), (61, 23))
	center = Point(*(viewport.size // 2))
	player.pos = Point(
			80 + random.randrange(world.size.width * world.cell((0, 0)).size.width - 80 * 2),
			80 + random.randrange(world.size.width * world.cell((0, 0)).size.width - 80 * 2),
			)
	world_shift = Point(0, 0)
	while True:
		window.clear()
		for field_index in world:
			field = world.cell(field_index)
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
			screen_control_points = [(world_shift + pos) - player.pos + center for pos in control_points]
			if not any(viewport.contains(screen_pos, with_border=True) for screen_pos in screen_control_points):
				continue
			for pos in field:
				screen_pos = world_shift + pos + field_rect.topleft - player.pos + center
				if not viewport.contains(screen_pos, with_border=True):
					continue
				window.addstr(screen_pos.y, screen_pos.x, field.cell(pos).sprite, COLORS[field.cell(pos).color])
		window.addstr(center.y, center.x, player.sprite.sprite, COLORS[player.sprite.color])

		hud_pos = viewport.right + 1
		window.addstr(0, hud_pos, "@{0};{1}".format(player.pos.x, player.pos.y))
		window.addstr(1, hud_pos, "hp:{0}/{1}".format(player.hp, player.max_hp))

		control = window.getch()
		if control == ord('q'):
			break
		elif chr(control) in MOVEMENT:
			new_pos = player.pos + MOVEMENT[chr(control)]
			world_boundaries = Rect(world_shift, Size(
				world.size.width * world.cell((0, 0)).size.width,
				world.size.height * world.cell((0, 0)).size.height,
				))
			world_expansion = Point(0, 0)
			if new_pos.x - center.x <= world_boundaries.left:
				world_expansion.x -= 1
			elif world_boundaries.right <= new_pos.x + center.x:
				world_expansion.x += 1
			if new_pos.y - center.y <= world_boundaries.top:
				world_expansion.y -= 1
			elif world_boundaries.bottom <= new_pos.y + center.y:
				world_expansion.y += 1
			if world_expansion:
				new_world = Matrix(world.size, None)
				for pos in new_world:
					old_pos = pos + world_expansion
					if world.valid(old_pos):
						new_world.set_cell(pos, world.cell(old_pos))
					else:
						new_world.set_cell(pos, generate_field())
				world = new_world
				world_shift += Point(
						world_expansion.x * world.cell((0, 0)).width,
						world_expansion.y * world.cell((0, 0)).height,
						)
			player.pos = new_pos

curses.wrapper(main)
