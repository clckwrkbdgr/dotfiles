from clckwrkbdgr import pcg
from ..monsters import Behavior
from ..engine.builders import Builder, UniformDistribution, WeightedDistribution
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
	DISTRIBUTION = UniformDistribution
	CELLS_PER_MONSTER = 60 # One monster for every 60 cells.
	MONSTERS = []
	CELLS_PER_ITEM = 180 # One item for every 180 cells.
	ITEMS = []

	def generate_actors(self):
		""" Places random population of different types of monsters.
		"""
		for _ in self.distribute(self.DISTRIBUTION, self.MONSTERS, self.amount_by_free_cells(self.CELLS_PER_MONSTER)):
			yield _
	def generate_items(self):
		""" Drops items in random locations. """
		for _ in self.distribute(self.DISTRIBUTION, self.ITEMS, self.amount_by_free_cells(self.CELLS_PER_ITEM)):
			yield _

class WeightedSquatters(Squatters):
	""" Like Squatters, except distributing items/monsters based on their weights.
	Lists MONSTERS and ITEMS should have additional first element - relative weight (int or float) for each item/monster.
	"""
	DISTRIBUTION = WeightedDistribution

class RogueDungeonSquatters(RogueDungeon, Squatters):
	pass

class RogueDungeonWeightedSquatters(RogueDungeon, WeightedSquatters):
	pass
