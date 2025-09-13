import math
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr import utils
from clckwrkbdgr.collections import AutoRegistry
from ..engine import builders

def place_square_tank(rng, grid, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	for x in range(size.width):
		for y in range(size.height):
			grid.set_cell(topleft_pos + (x, y), 'wall')

def place_round_tank(rng, grid, topleft_pos, size):
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

def place_broken_tank(rng, grid, topleft_pos, size):
	size = Size(size)
	topleft_pos = Point(topleft_pos)
	for x in range(size.width):
		for y in range(size.height):
			if rng.choice((False, True)):
				grid.set_cell(topleft_pos + (x, y), 'wall')

class Builder(builders.Builder):
	def is_open(self, pos):
		return self.grid.cell(pos) == 'floor'
	def generate_appliances(self):
		yield self.point(self.is_accessible), 'start'
		yield self.point(self.is_accessible), 'overworld_exit'

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
			field_shift.x += self.rng.randrange((grid.width - 2) - array_size.width)
		if (grid.height - 2) > array_size.height:
			field_shift.y += self.rng.randrange((grid.height - 2) - array_size.height)
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
				place_form = self.rng.choice(forms)
				place_form(self.rng, grid, tank_topleft, tank_size)

class Builders:
	def __init__(self, builders, rng=None):
		self.rng = rng or RNG()
		self.builder_types = builders
	def build_block(self, block):
		builder_type = self.rng.choice(self.builder_types)
		builder = builder_type(self.rng, block)
		builder.generate()
		builder.make_grid()
		appliances = list(builder.make_appliances())
		self._start_pos = next(_.pos for _ in appliances if _.obj == 'start')
		self.appliances = [_ for _ in appliances if _.obj != 'start']
