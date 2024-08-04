from ..utils import Enum
from . import _base as pcg

class Behavior(Enum):
	""" PLAYER
	DUMMY
	INERT
	ANGRY
	"""

class Settler(object):
	def __init__(self, rng, builder):
		self.rng = rng
		self.builder = builder
	def populate(self):
		self.monsters = []
		self._populate()
	def _populate(self): # pragma: no cover
		raise NotImplementedError()

class SingleMonster(Settler):
	def _populate(self):
		passable = lambda pos: self.builder.strata.cell(pos.x, pos.y).terrain.passable
		pos = pcg.pos(self.rng, self.builder.strata.size, lambda pos: passable(pos) and pos not in [self.builder.start_pos, self.builder.exit_pos])
		self.monsters.append(('monster', Behavior.ANGRY, pos))
