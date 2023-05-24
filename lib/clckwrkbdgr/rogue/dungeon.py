import random
from clckwrkbdgr.math import Point, Matrix

class Dungeon:
	def __init__(self):
		self.terrain = Matrix((25, 25), '.')
		for _ in range((self.terrain.width * self.terrain.height) // 3):
			pos = Point(random.randrange(self.terrain.width), random.randrange(self.terrain.height))
			self.terrain.set_cell(pos, '#')
		self.rogue = Point(12, 12)
	def get_sprite(self, pos):
		if pos == self.rogue:
			return "@"
		return self.terrain.cell(pos)
	def control(self, control):
		if isinstance(control, type) and issubclass(control, BaseException):
			control = control()
		if isinstance(control, BaseException):
			raise control
		if isinstance(control, Point):
			new_pos = self.rogue + control
			if self.terrain.valid(new_pos) and self.terrain.cell(new_pos) == '.':
				self.rogue = new_pos

