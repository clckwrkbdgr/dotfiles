import random
from clckwrkbdgr.math import Point, Size, Matrix

class Strata:
	def __init__(self, block_size, builder):
		self.builder = builder
		self.block_size = Size(block_size)
		self.shift = Point(0, 0) - self.block_size
		self.blocks = Matrix((3, 3))
		for row in range(self.blocks.height):
			for col in range(self.blocks.width):
				self.blocks.set_cell((col, row), Matrix(self.block_size, '.'))
				self.builder.build_block(self.blocks.cell((col, row)))
	def cell(self, pos):
		relative_pos = Point(pos) - self.shift
		block_pos = Point(relative_pos.x // self.block_size.width, relative_pos.y // self.block_size.height)
		if not self.blocks.valid(block_pos):
			return ' '
		block = self.blocks.cell(block_pos)
		block_rel_pos = Point(relative_pos.x % self.block_size.width, relative_pos.y % self.block_size.height)
		return block.cell(block_rel_pos)
	def is_passable(self, pos):
		return self.cell(pos) == '.'
	def recalibrate(self, anchor_pos):
		relative_pos = Point(anchor_pos) - self.shift
		block_pos = Point(relative_pos.x // self.block_size.width, relative_pos.y // self.block_size.height)
		if block_pos == Point(1, 1):
			return
		block_shift = block_pos - Point(1, 1)
		new_blocks = Matrix((3, 3))
		for row in range(new_blocks.height):
			for col in range(new_blocks.width):
				pos = Point(col, row)
				old_pos = pos + block_shift
				if self.blocks.valid(old_pos):
					new_blocks.set_cell(pos, self.blocks.cell(old_pos))
				else:
					new_blocks.set_cell(pos, Matrix(self.block_size, '.'))
					self.builder.build_block(new_blocks.cell(pos))
		self.blocks = new_blocks
		self.shift += Point(
				block_shift.x * self.block_size.width,
				block_shift.y * self.block_size.height,
				)

class Builder:
	def build_block(self, block):
		for _ in range((block.width * block.height) // 3):
			pos = Point(random.randrange(block.width), random.randrange(block.height))
			block.set_cell(pos, '#')
	def place_rogue(self, terrain):
		return Point(terrain.block_size.width // 2, terrain.block_size.height // 2)

class Dungeon:
	BLOCK_SIZE = Size(32, 32)

	def __init__(self, builder=None):
		self.builder = builder or Builder()
		self.terrain = Strata(block_size=self.BLOCK_SIZE, builder=self.builder)
		self.rogue = Point(self.builder.place_rogue(self.terrain))
	def get_sprite(self, pos):
		if pos == Point(0, 0):
			return "@"
		pos = Point(pos) + self.rogue
		return self.terrain.cell(pos)
	def control(self, control):
		if isinstance(control, type) and issubclass(control, BaseException):
			control = control()
		if isinstance(control, BaseException):
			raise control
		if isinstance(control, Point):
			new_pos = self.rogue + control
			if self.terrain.is_passable(new_pos):
				self.rogue = new_pos
				self.terrain.recalibrate(self.rogue)

