from . import _base as pcg
from ..monsters import Behavior

class Settler(object):
	""" Base class to populate terrain with monsters and other objects.

	Override methods _populate() and _place_items() to do actual jobs.
	"""
	def __init__(self, rng, builder):
		""" Creates settler over builder with already generated and filled map.
		To actually fill dungeon, call populate().
		"""
		self.rng = rng
		self.builder = builder
	def populate(self):
		""" Places monsters, items and other objects all over map, according to custom overrides.

		Creates list .monsters with data for each monster in form of tuple: (pos, ...other data).

		Creates list .items with data for each item in form of tuple: (pos, ...other data).

		Values should be replaced later with actual objects in the Game class itself.
		"""
		self.monsters = []
		self._populate()
		self.items = []
		self._place_items()
	def _populate(self): # pragma: no cover
		""" Should fill array of .monsters """
		raise NotImplementedError()
	def _place_items(self): # pragma: no cover
		""" Should fill array of .items
		Default implementation places no items.
		"""
		pass

class SingleMonster(Settler):
	""" Single monster. """
	def _populate(self):
		""" Places monster at first passable terrain. """
		passable = lambda pos: self.builder.strata.cell(pos.x, pos.y).terrain.passable
		pos = pcg.pos(self.rng, self.builder.strata.size, lambda pos: passable(pos) and pos not in [self.builder.start_pos, self.builder.exit_pos])
		self.monsters.append(('monster', Behavior.ANGRY, pos))

class Squatters(Settler):
	""" Set of squatters, randomly distributed throughout the map.
	"""
	def is_passable(self, pos):
		""" True if terrain is passable. """
		return self.builder.strata.cell(pos.x, pos.y).terrain.passable
	def is_free(self, pos):
		""" True if not occupied by any other object/monster. """
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
		""" Places random population of three different types of monsters:
		dummy plants, inert slime monsters and angry rodents.
		"""
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
		""" Drops healing potions in random locations. """
		total_passable_cells = sum(1 for pos in self.builder.strata.size if self.is_passable(pos))
		ratio = 1 / 180. # One healing potion for 180 cells, or one for 3 monsters.
		total_items = int(total_passable_cells * ratio)
		for _ in range(total_items):
			pos = pcg.pos(self.rng, self.builder.strata.size, self.is_free)
			self.items.append(('healing potion', pos))
