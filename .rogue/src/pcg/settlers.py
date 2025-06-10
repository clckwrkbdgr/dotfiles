from clckwrkbdgr import pcg
from ..monsters import Behavior
from .builders import Builder, CustomMap, RogueDungeon

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
	def _populate(self):
		self.builder.rng.choice([1]) # FIXME mock action just to shift RNG
		self.monsters += self.MONSTERS
	def _place_items(self):
		self.items += self.ITEMS

class SingleMonster(Settler):
	""" Single monster.

	Data should be defined in class field MONSTER as tuple:
	MONSTER = ('monster_type_id', <args...>)
	"""
	MONSTER = None

	def passable(self, pos):
		return self.strata.cell(pos) in self.PASSABLE
	def _populate(self):
		""" Places monster at first passable terrain. """
		self.builder.rng.choice([1]) # FIXME mock action just to shift RNG
		pcg.point(self.builder.rng, self.strata.size) # FIXME work around legacy bug which scrapped the first result
		pos = pcg.TryCheck(pcg.point).check(lambda pos: self.passable(pos) and pos not in [self.start_pos, self.exit_pos])(self.builder.rng, self.strata.size)
		self.monsters.append(self.MONSTER + (pos,))

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

	def is_passable(self, pos):
		""" True if terrain is passable. """
		return self.strata.cell(pos) in self.PASSABLE
	def is_free(self, pos):
		""" True if not occupied by any other object/monster. """
		if not self.is_passable(pos):
			return False
		if pos == self.start_pos:
			return False
		if pos == self.exit_pos:
			return False
		if pos in self.monster_cells:
			return False
		return True
	def _choice(self, entries):
		return self.builder.rng.choice(entries) if len(entries) != 1 else entries[0]
	def _populate(self):
		""" Places random population of different types of monsters.
		"""
		total_passable_cells = sum(1 for pos in self.strata.size.iter_points() if self.is_passable(pos))
		total_monsters = int(total_passable_cells / float(self.CELLS_PER_MONSTER))
		self.monster_cells = set()
		if not self.MONSTERS:
			return
		for _ in range(total_monsters):
			pcg.point(self.builder.rng, self.strata.size) # FIXME work around legacy bug which scrapped the first result
			pos = pcg.TryCheck(pcg.point).check(self.is_free)(self.builder.rng, self.strata.size)
			self.monster_cells.add(pos)
			self.monsters.append(self._choice(self.MONSTERS) + (pos,))
	def _place_items(self):
		""" Drops items in random locations. """
		total_passable_cells = sum(1 for pos in self.strata.size.iter_points() if self.is_passable(pos))
		total_items = int(total_passable_cells / float(self.CELLS_PER_ITEM))
		if not self.ITEMS:
			return
		for _ in range(total_items):
			pcg.point(self.builder.rng, self.strata.size) # FIXME work around legacy bug which scrapped the first result
			pos = pcg.TryCheck(pcg.point).check(self.is_free)(self.builder.rng, self.strata.size)
			self.items.append(self._choice(self.ITEMS) + (pos,))

class WeightedSquatters(Squatters):
	""" Like Squatters, except distributing items/monsters based on their weights.
	Lists MONSTERS and ITEMS should have additional first element - relative weight (int or float) for each item/monster.
	"""
	def _choice(self, entries):
		from clckwrkbdgr import pcg
		return pcg.weighted_choices(self.builder.rng, [(data[0], data[1:]) for data in entries])[0]

class RogueDungeonSquatters(RogueDungeon, Squatters):
	pass

class RogueDungeonWeightedSquatters(RogueDungeon, WeightedSquatters):
	pass
