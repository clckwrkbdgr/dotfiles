from . import _base as pcg
from ..monsters import Behavior

class Settler(object):
	def __init__(self, rng, builder):
		self.rng = rng
		self.builder = builder
	def populate(self):
		self.monsters = []
		self._populate()
		self.items = []
		self._place_items()
	def _populate(self): # pragma: no cover
		raise NotImplementedError()
	def _place_items(self): # pragma: no cover
		pass

class SingleMonster(Settler):
	def _populate(self):
		passable = lambda pos: self.builder.strata.cell(pos.x, pos.y).terrain.passable
		pos = pcg.pos(self.rng, self.builder.strata.size, lambda pos: passable(pos) and pos not in [self.builder.start_pos, self.builder.exit_pos])
		self.monsters.append(('monster', Behavior.ANGRY, pos))

class Squatters(Settler):
	def is_passable(self, pos):
		return self.builder.strata.cell(pos.x, pos.y).terrain.passable
	def is_free(self, pos):
		if not self.is_passable(pos):
			return False
		if pos == self.builder.start_pos:
			return False
		if pos == self.builder.exit_pos:
			return False
		if pos in self.monster_cells:
			return False
		return True
	def _populate(self):
		total_passable_cells = sum(1 for pos in self.builder.strata.size if self.is_passable(pos))
		ratio = 1 / 60. # One monster for 60 cells.
		total_monsters = int(total_passable_cells * ratio)
		self.monster_cells = set()
		dwellers = [
				('plant', Behavior.DUMMY),
				('slime', Behavior.INERT),
				('rodent', Behavior.ANGRY),
				]
		for _ in range(total_monsters):
			pos = pcg.pos(self.rng, self.builder.strata.size, self.is_free)
			self.monster_cells.add(pos)
			self.monsters.append(self.rng.choice(dwellers) + (pos,))
	def _place_items(self):
		total_passable_cells = sum(1 for pos in self.builder.strata.size if self.is_passable(pos))
		ratio = 1 / 180. # One healing potion for 180 cells, or one for 3 monsters.
		total_items = int(total_passable_cells * ratio)
		for _ in range(total_items):
			pos = pcg.pos(self.rng, self.builder.strata.size, self.is_free)
			self.items.append(('healing potion', pos))
