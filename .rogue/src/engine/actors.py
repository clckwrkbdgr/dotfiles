from clckwrkbdgr.math import Point
from clckwrkbdgr.utils import classfield

class Monster(object):
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown creature')

	def __init__(self, pos): # pragma: no cover -- TODO
		self.pos = Point(pos) if pos else None
