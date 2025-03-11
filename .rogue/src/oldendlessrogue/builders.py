import random
import math
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.collections import AutoRegistry

def place_square_tank(field, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	for x in range(size.width):
		for y in range(size.height):
			field.set_cell(topleft_pos + (x, y), '#')

def place_round_tank(field, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	center = Point(
			size.width / 2,
			size.height / 2,
			) - Point(0.5, 0.5)
	radius = min(size.width / 2, size.height / 2)
	for x in range(size.width):
		for y in range(size.height):
			if math.hypot(x - center.x, y - center.y) > radius:
				continue
			field.set_cell(topleft_pos + (x, y), '#')

def place_broken_tank(field, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	for x in range(size.width):
		for y in range(size.height):
			if random.choice((False, True)):
				field.set_cell(topleft_pos + (x, y), '#')

builders = AutoRegistry()

@builders()
def fill_with_garbage(field):
	for _ in range((field.width * field.height) // 3):
		pos = Point(random.randrange(field.width), random.randrange(field.height))
		field.set_cell(pos, '#')

@builders()
def empty_square(field):
	pos = Point(random.randrange(field.width), random.randrange(field.height))
	field.set_cell(pos, '#')

@builders()
def field_of_tanks(field):
	tank_size = Size(4, 4)
	tank_count = Size(
			(field.width - 2) // (tank_size.width + 1),
			(field.height - 2) // (tank_size.height + 1),
			)
	array_size = Size(
			tank_count.width * (tank_size.width + 1),
			tank_count.height * (tank_size.height + 1),
			)
	field_shift = Point(1, 1)
	if (field.width - 2) > array_size.width:
		field_shift.x += random.randrange((field.width - 2) - array_size.width)
	if (field.height - 2) > array_size.height:
		field_shift.y += random.randrange((field.height - 2) - array_size.height)
	forms = [
			place_square_tank,
			place_round_tank,
			place_broken_tank,
			]
	for col in range(tank_count.width):
		for row in range(tank_count.width):
			tank_topleft = field_shift + Point(
					col * (tank_size.width + 1),
					row * (tank_size.height + 1),
					)
			place_form = random.choice(forms)
			place_form(field, tank_topleft, tank_size)

class Builders:
	def build_block(self, block):
		builder_name = random.choice(list(builders.keys()))
		builder_function = builders[builder_name]
		builder_function(block)
	def place_rogue(self, terrain):
		return Point(terrain.block_size.width // 2, terrain.block_size.height // 2)
