from . import _base as pcg
from ..monsters import Behavior

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

class Squatters(Settler):
	def _populate(self):
		passable = lambda pos: self.builder.strata.cell(pos.x, pos.y).terrain.passable
		total_passable_cells = sum(1 for pos in self.builder.strata.size if passable(pos))
		ratio = 1 / 60. # One monster for 20 cells.
		total_monsters = int(total_passable_cells * ratio)
		used_cells = set()
		dwellers = [
				('plant', Behavior.DUMMY),
				('slime', Behavior.INERT),
				('rodent', Behavior.ANGRY),
				]
		for _ in range(total_monsters):
			pos = pcg.pos(self.rng, self.builder.strata.size, lambda pos: passable(pos) and pos not in used_cells and pos not in [self.builder.start_pos, self.builder.exit_pos])
			used_cells.add(pos)
			self.monsters.append(self.rng.choice(dwellers) + (pos,))
