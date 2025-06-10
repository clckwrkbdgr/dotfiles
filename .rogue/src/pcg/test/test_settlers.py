import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from .. import settlers, builders
from ... import monsters
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.pcg import RNG

class MockSettler(settlers.Settler):
	def _build(self, grid):
		pass
	def _populate(self, grid):
		self.monsters.append(('monster', settlers.Behavior.DUMMY, Point(1, 2)))

class TestSettler(unittest.TestCase):
	def should_populate_dungeon(self):
		rng = RNG(0)
		settler = MockSettler(rng, Size(20, 20))
		settler.build()
		self.assertEqual(settler.monsters, [
			('monster', settlers.Behavior.DUMMY, Point(1, 2)),
			])

class TestSquatters(unittest.TestCase):
	def _make_terrain(self, builder):
		from ...game import Game # FIXME circular dependency
		from ...terrain import Cell, Terrain # FIXME circular dependency
		class MockRogueDungeon(Game):
			TERRAIN = {
				None : Terrain(' ', ' ', False),
				'corner' : Terrain('corner', "+", False, remembered='+'),
				'rogue_door' : Terrain('rogue_door', "+", True, remembered='+', allow_diagonal=False, dark=True),
				'floor' : Terrain('floor', ".", True),
				'rogue_passage' : Terrain('rogue_passage', "#", True, remembered='#', allow_diagonal=False, dark=True),
				'wall_h' : Terrain('wall_h', "-", False, remembered='-'),
				'wall_v' : Terrain('wall_v', "|", False, remembered='|'),
				}
		for pos in builder.strata.size.iter_points():
			builder.strata.set_cell(
					pos,
					Cell(MockRogueDungeon.TERRAIN[builder.strata.cell(pos)]),
					)
	def should_check_availability_of_placement_position(self):
		rng = RNG(0)
		builder = settlers.RogueDungeonSquatters(rng, Size(80, 25))
		builder.PASSABLE = ('floor',)
		settler = builder
		builder.build()

		self.assertTrue(settler.is_passable(builder.strata, Point(8, 2)))
		self.assertFalse(settler.is_passable(builder.strata, Point(1, 1)))
		self.assertFalse(settler.is_passable(builder.strata, Point(8, 1)))

		settler.monster_cells = set([Point(7, 3)])
		self.assertTrue(settler.is_free(builder.strata, Point(8, 2)))
		self.assertFalse(settler.is_free(builder.strata, Point(1, 1)))
		self.assertFalse(settler.is_free(builder.strata, Point(8, 1)))
		self.assertFalse(settler.is_free(builder.strata, next(iter(settler.monster_cells))))
		self.assertFalse(settler.is_free(builder.strata, builder.start_pos))
		self.assertFalse(settler.is_free(builder.strata, builder.exit_pos))
	def should_populate_dungeon_with_squatters(self):
		rng = RNG(0)
		class _MockSquatters(settlers.RogueDungeonSquatters):
			MONSTERS = [
					('plant', monsters.Behavior.DUMMY),
					('slime', monsters.Behavior.INERT),
					('rodent', monsters.Behavior.ANGRY),
					]
			ITEMS = [
					('healing potion',),
					]
			PASSABLE = ('floor',)
		builder = _MockSquatters(rng, Size(80, 25))
		builder.build()
		settler = builder
		self._make_terrain(builder)

		self.maxDiff = None
		self.assertEqual(settler.monsters, [
			('rodent', 3, Point(59, 18)),
			('plant', 1,  Point(68, 12)),
			('rodent', 3, Point(33, 9)),
			('plant', 1,  Point(34, 11)),
			('rodent', 3, Point(9, 19)),
			('plant', 1,  Point(22, 19))
			])
		self.assertEqual(settler.items, [
			('healing potion', Point(31, 19)),
			('healing potion', Point(17, 19)),
			])
	def should_populate_dungeon_with_weighted_squatters(self):
		rng = RNG(0)
		class _MockSquatters(settlers.RogueDungeonWeightedSquatters):
			MONSTERS = [
					(1, 'plant', monsters.Behavior.DUMMY),
					(5, 'slime', monsters.Behavior.INERT),
					(10, 'rodent', monsters.Behavior.ANGRY),
					]
			ITEMS = [
					(1, 'healing potion',),
					]
			PASSABLE = ('floor',)
		builder = _MockSquatters(rng, Size(80, 25))
		builder.build()
		settler = builder
		self._make_terrain(builder)

		self.maxDiff = None
		self.assertEqual(settler.monsters, [
			('rodent', 3, Point(59, 18)),
			('slime', 2,  Point(68, 12)),
			('rodent', 3, Point(33, 9)),
			('slime', 2,  Point(34, 11)),
			('rodent', 3, Point(9, 19)),
			('slime', 2,  Point(22, 19))
			])
		self.assertEqual(settler.items, [
			('healing potion', Point(31, 19)),
			('healing potion', Point(63, 4)),
			])
