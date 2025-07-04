from clckwrkbdgr.math import Point
from clckwrkbdgr.utils import classfield

class Monster(object):
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown creature')

	def __init__(self, pos):
		self.pos = Point(pos) if pos else None
	def __str__(self):
		return self.name
	def __repr__(self):
		return '{0}({1} @{2})'.format(type(self).__name__, self.name, self.pos)
