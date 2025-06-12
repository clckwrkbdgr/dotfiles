from clckwrkbdgr import pcg
from ..monsters import Behavior
from ..engine.builders import Builder
from .builders import CustomMap, RogueDungeon

class Settler(Builder):
	PASSABLE = None
	pass

class CustomSettler(CustomMap):
	""" Fills map with predetermined monsters and items.
	Data should be provided as list of raw parameters:
	(<item/monster data>, <pos>)
	"""
	MONSTERS = [
			]
	ITEMS = [
			]
	def generate_actors(self, grid):
		self.rng.choice([1]) # FIXME mock action just to shift RNG
		for _ in self.MONSTERS:
			yield _
	def generate_items(self, grid):
		for _ in self.ITEMS:
			yield _

class SingleMonster(Settler):
	""" Single monster.

	Data should be defined in class field MONSTER as tuple:
	MONSTER = ('monster_type_id', <args...>)
	"""
	MONSTER = None

	def passable(self, grid, pos):
		return grid.cell(pos) in self.PASSABLE
	def generate_actors(self, grid):
		""" Places monster at first passable terrain. """
		self.rng.choice([1]) # FIXME mock action just to shift RNG
		pcg.point(self.rng, grid.size) # FIXME work around legacy bug which scrapped the first result
		pos = pcg.TryCheck(pcg.point).check(lambda pos: self.passable(grid, pos) and pos not in [self.start_pos, self.exit_pos])(self.rng, grid.size)
		yield (pos,) + self.MONSTER

class CustomMapSingleMonster(CustomMap, SingleMonster):
	pass

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

	def is_passable(self, grid, pos):
		""" True if terrain is passable. """
		return grid.cell(pos) in self.PASSABLE
	def is_free(self, grid, pos):
		""" True if not occupied by any other object/monster. """
		if not self.is_passable(grid, pos):
			return False
		if pos == self.start_pos:
			return False
		if pos == self.exit_pos:
			return False
		if pos in self.monster_cells:
			return False
		return True
	def _choice(self, entries):
		return self.rng.choice(entries) if len(entries) != 1 else entries[0]
	def generate_actors(self, grid):
		""" Places random population of different types of monsters.
		"""
		total_passable_cells = sum(1 for pos in grid.size.iter_points() if self.is_passable(grid, pos))
		total_monsters = int(total_passable_cells / float(self.CELLS_PER_MONSTER))
		self.monster_cells = set()
		if not self.MONSTERS:
			return
		for _ in range(total_monsters):
			pcg.point(self.rng, grid.size) # FIXME work around legacy bug which scrapped the first result
			pos = pcg.TryCheck(pcg.point).check(lambda _p: self.is_free(grid, _p))(self.rng, grid.size)
			self.monster_cells.add(pos)
			yield (pos,) + self._choice(self.MONSTERS)
	def generate_items(self, grid):
		""" Drops items in random locations. """
		total_passable_cells = sum(1 for pos in grid.size.iter_points() if self.is_passable(grid, pos))
		total_items = int(total_passable_cells / float(self.CELLS_PER_ITEM))
		if not self.ITEMS:
			return
		for _ in range(total_items):
			pcg.point(self.rng, grid.size) # FIXME work around legacy bug which scrapped the first result
			pos = pcg.TryCheck(pcg.point).check(lambda _p: self.is_free(grid, _p))(self.rng, grid.size)
			yield (pos,) + self._choice(self.ITEMS)

class WeightedSquatters(Squatters):
	""" Like Squatters, except distributing items/monsters based on their weights.
	Lists MONSTERS and ITEMS should have additional first element - relative weight (int or float) for each item/monster.
	"""
	def _choice(self, entries):
		from clckwrkbdgr import pcg
		return pcg.weighted_choices(self.rng, [(data[0], data[1:]) for data in entries])[0]

class RogueDungeonSquatters(RogueDungeon, Squatters):
	pass

class RogueDungeonWeightedSquatters(RogueDungeon, WeightedSquatters):
	pass
