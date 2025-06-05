import random
import math
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr import utils
from clckwrkbdgr.collections import AutoRegistry
from src.engine import builders

def place_square_tank(grid, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	for x in range(size.width):
		for y in range(size.height):
			grid.set_cell(topleft_pos + (x, y), 'wall')

def place_round_tank(grid, topleft_pos, size):
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
			grid.set_cell(topleft_pos + (x, y), 'wall')

def place_broken_tank(grid, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	for x in range(size.width):
		for y in range(size.height):
			if random.choice((False, True)):
				grid.set_cell(topleft_pos + (x, y), 'wall')

class Builder(builders.Builder):
	class Mapping:
		floor = '.'
		wall = '#'

class FilledWithGarbage(Builder):
	def fill_grid(self, grid):
		grid.clear('floor')
		for _ in range((grid.width * grid.height) // 3):
			pos = self.point()
			grid.set_cell(pos, 'wall')

class EmptySquare(Builder):
	def fill_grid(self, grid):
		grid.clear('floor')
		pos = self.point()
		grid.set_cell(pos, 'wall')

class FieldOfTanks(Builder):
	def fill_grid(self, grid):
		grid.clear('floor')
		tank_size = Size(4, 4)
		tank_count = Size(
				(grid.width - 2) // (tank_size.width + 1),
				(grid.height - 2) // (tank_size.height + 1),
				)
		array_size = Size(
				tank_count.width * (tank_size.width + 1),
				tank_count.height * (tank_size.height + 1),
				)
		field_shift = Point(1, 1)
		if (grid.width - 2) > array_size.width:
			field_shift.x += random.randrange((grid.width - 2) - array_size.width)
		if (grid.height - 2) > array_size.height:
			field_shift.y += random.randrange((grid.height - 2) - array_size.height)
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
				place_form(grid, tank_topleft, tank_size)

class Builders:
	def build_block(self, block):
		builder_type = random.choice(utils.all_subclasses(Builder))
		builder = builder_type(random, block)
		builder.generate()
		builder.make_grid()
	def place_rogue(self, terrain):
		return Point(terrain.block_size.width // 2, terrain.block_size.height // 2)
