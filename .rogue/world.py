from clckwrkbdgr.math import Size
from clckwrkbdgr import utils
from src.engine import builders
import src.world.dungeonbuilders
import src.world.roguedungeon
from src.world import endlessbuilders, endlessdungeon
from src.world import overworld
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *

class DungeonMapping(TerrainMapping, QuestMapping, ItemMapping, MonsterMapping, ObjectMapping):
	pass

class DungeonSquatters(builders.Builder):
	""" Set of squatters, randomly distributed throughout the map
	based on their relative weights (int or float) within corresponding
	distribution list.

	Data should be defined in class fields MONSTERS and ITEMS as lists of tuples:
	MONSTERS = (<weight>, 'monster_type_id', <args...>)
	ITEMS = (<weight>, 'item_type_id', <args...>)

	Distribution is controlled by corresponding CELLS_PER_* fields, which should
	set amount of _free_ (i.e. passable) cells that support one monster/item.
	"""
	CELLS_PER_MONSTER = 60 # One monster for every 60 cells.
	MONSTERS = [
			(1, ('carnivorous_plant',)),
			(3, ('slime',)),
			(10, ('rodent',)),
			]
	CELLS_PER_ITEM = 180 # One item for every 180 cells.
	ITEMS = [
			(1, ('HealingPotion',)),
			]
	def is_open(self, pos):
		return self.grid.cell(pos) == 'floor'
	def generate_actors(self):
		""" Places random population of different types of monsters.
		"""
		for _ in self.distribute(builders.WeightedDistribution, self.MONSTERS, self.amount_by_free_cells(self.CELLS_PER_MONSTER)):
			yield _
	def generate_items(self):
		""" Drops items in random locations. """
		for _ in self.distribute(builders.WeightedDistribution, self.ITEMS, self.amount_by_free_cells(self.CELLS_PER_ITEM)):
			yield _

class BSPDungeon(src.world.dungeonbuilders.BSPDungeon, DungeonSquatters):
	Mapping = DungeonMapping
class CityBuilder(src.world.dungeonbuilders.CityBuilder, DungeonSquatters):
	Mapping = DungeonMapping
class Sewers(src.world.dungeonbuilders.Sewers, DungeonSquatters):
	Mapping = DungeonMapping
class RogueDungeon(src.world.dungeonbuilders.RogueDungeon, DungeonSquatters):
	Mapping = DungeonMapping
class CaveBuilder(src.world.dungeonbuilders.CaveBuilder, DungeonSquatters):
	Mapping = DungeonMapping
class MazeBuilder(src.world.dungeonbuilders.MazeBuilder, DungeonSquatters):
	Mapping = DungeonMapping

class EndlessBuilder:
	Mapping = DungeonMapping

class FieldOfTanks(EndlessBuilder, endlessbuilders.FieldOfTanks):
	pass
class EmptySquare(EndlessBuilder, endlessbuilders.EmptySquare):
	pass
class FilledWithGarbage(EndlessBuilder, endlessbuilders.FilledWithGarbage):
	pass

class EndlessScene(endlessdungeon.Scene):
	BUILDERS = lambda: endlessbuilders.Builders(utils.all_subclasses(EndlessBuilder))

class RogueBuilder(src.world.roguedungeon.Builder):
	Mapping = DungeonMapping
	def get_item_distribution(self, depth):
		return [
		(50, HealingPotion),
		(depth, Dagger),
		(depth // 2, Sword),
		(max(0, (depth-5) // 3), Axe),
		(depth, Rags),
		(depth // 2, Leather),
		(max(0, (depth-5) // 3), ChainMail),
		(max(0, (depth-10) // 3), PlateArmor),
		]
	def get_monster_distribution(self, depth):
		return itertools.chain(
				easy_monsters.get_distribution(depth),
				norm_monsters.get_distribution(depth),
				hard_monsters.get_distribution(depth),
				)

class RogueDungeonScene(src.world.roguedungeon.Scene):
	MAX_LEVELS = 26
	SIZE = Size(78, 21)
	BUILDER = RogueBuilder

class OverBuilder(object):
	Mapping = DungeonMapping

class Forest(OverBuilder, overworld.Forest): pass
class Desert(OverBuilder, overworld.Desert): pass
class Thundra(OverBuilder, overworld.Thundra): pass
class Marsh(OverBuilder, overworld.Marsh): pass
