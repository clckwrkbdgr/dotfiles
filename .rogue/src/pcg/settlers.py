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
	""" Single monster.

	Data should be defined in class field MONSTER as tuple:
	MONSTER = ('monster_type_id', <args...>)
	"""
	MONSTER = None

	def _populate(self):
		""" Places monster at first passable terrain. """
		passable = lambda pos: self.builder.strata.cell(pos.x, pos.y).terrain.passable
		pos = pcg.pos(self.rng, self.builder.strata.size, lambda pos: passable(pos) and pos not in [self.builder.start_pos, self.builder.exit_pos])
		self.monsters.append(self.MONSTER + (pos,))

class Squatters(Settler):
	""" Set of squatters, randomly distributed throughout the map.

	Data should be defined in class fields MONSTERS and ITEMS as lists of tuples:
	MONSTERS = ('monster_type_id', <args...>)
	ITEMS = ('item_type_id', <args...>)

	Distribution is controlled by corresponding CELLS_PER_* fields, which should
	set amount of _free_ (i.e. passable) cells that support one monster/item.
	"""
	CELLS_PER_MONSTER = 60 # One monster for every 60 cells.
	MONSTERS = []
	CELLS_PER_ITEM = 180 # One item for every 180 cells.
	ITEMS = []

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
	def _choice(self, entries):
		return self.rng.choice(entries) if len(entries) != 1 else entries[0]
	def _populate(self):
		""" Places random population of different types of monsters.
		"""
		total_passable_cells = sum(1 for pos in self.builder.strata.size if self.is_passable(pos))
		total_monsters = int(total_passable_cells / float(self.CELLS_PER_MONSTER))
		self.monster_cells = set()
		for _ in range(total_monsters):
			pos = pcg.pos(self.rng, self.builder.strata.size, self.is_free)
			self.monster_cells.add(pos)
			self.monsters.append(self._choice(self.MONSTERS) + (pos,))
	def _place_items(self):
		""" Drops items in random locations. """
		total_passable_cells = sum(1 for pos in self.builder.strata.size if self.is_passable(pos))
		total_items = int(total_passable_cells / float(self.CELLS_PER_ITEM))
		for _ in range(total_items):
			pos = pcg.pos(self.rng, self.builder.strata.size, self.is_free)
			self.items.append(self._choice(self.ITEMS) + (pos,))

class WeightedSquatters(Squatters):
	""" Like Squatters, except distributing items/monsters based on their weights.
	Lists MONSTERS and ITEMS should have additional first element - relative weight (int or float) for each item/monster.
	"""
	def _choice(self, entries):
		return pcg.weighted_choices(self.rng, [(data[0], data[1:]) for data in entries])[0]
