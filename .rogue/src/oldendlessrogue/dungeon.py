from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.math.grid import EndlessMatrix
from . import builders

class Dungeon(object):
	BLOCK_SIZE = Size(32, 32)

	def __init__(self, builder=None):
		self.builder = builder or builders.Builders()
		self.terrain = EndlessMatrix(block_size=self.BLOCK_SIZE, builder=self.builder.build_block)
		self.rogue = Point(self.builder.place_rogue(self.terrain))
		self.time = 0
	def __getstate__(self):
		return self.__dict__
	def __setstate__(self, state):
		self.__dict__.update(state)
		if 'time' not in state:
			self.time = 0
		self.terrain.builder = self.builder.build_block
	def get_sprite(self, pos):
		if pos == Point(0, 0):
			return "@"
		pos = Point(pos) + self.rogue
		return self.terrain.cell(pos)
	def is_passable(self, pos):
		return self.terrain.cell(pos) == '.'
	def control(self, control):
		if isinstance(control, type) and issubclass(control, BaseException):
			control = control()
		if isinstance(control, BaseException):
			raise control
		if isinstance(control, Point):
			new_pos = self.rogue + control
			if self.is_passable(new_pos):
				self.rogue = new_pos
				self.terrain.recalibrate(self.rogue)
			self.time += 1
