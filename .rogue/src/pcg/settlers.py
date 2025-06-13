from clckwrkbdgr import pcg
from ..monsters import Behavior
from ..engine.builders import Builder
from .builders import CustomMap, RogueDungeon

class Settler(Builder):
	PASSABLE = None
	def is_open(self, pos):
		""" True if terrain is passable. """
		return self.grid.cell(pos) in self.PASSABLE

class CustomSettler(CustomMap):
	""" Fills map with predetermined monsters and items.
	Data should be provided as list of raw parameters:
	(<item/monster data>, <pos>)
	"""
	MONSTERS = [
			]
	ITEMS = [
			]
	def generate_actors(self):
		self.rng.choice([1]) # FIXME mock action just to shift RNG
		for _ in self.MONSTERS:
			yield _
	def generate_items(self):
		for _ in self.ITEMS:
			yield _

class SingleMonster(Settler):
	""" Single monster.

	Data should be defined in class field MONSTER as tuple:
	MONSTER = ('monster_type_id', <args...>)
	"""
	MONSTER = None

	def generate_actors(self):
		""" Places monster at first passable terrain. """
		yield (self.point(self.is_free),) + self.MONSTER

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

	def _choice(self, entries):
		return self.rng.choice(entries) if len(entries) != 1 else entries[0]
	def generate_actors(self):
		""" Places random population of different types of monsters.
		"""
		total_passable_cells = sum(1 for pos in self.grid.size.iter_points() if self.is_open(pos))
		total_monsters = int(total_passable_cells / float(self.CELLS_PER_MONSTER))
		for _ in range(total_monsters):
			yield (self.point(self.is_free),) + self._choice(self.MONSTERS)
	def generate_items(self):
		""" Drops items in random locations. """
		total_passable_cells = sum(1 for pos in self.grid.size.iter_points() if self.is_free(pos))
		total_items = int(total_passable_cells / float(self.CELLS_PER_ITEM))
		for _ in range(total_items):
			yield (self.point(self.is_free),) + self._choice(self.ITEMS)

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
