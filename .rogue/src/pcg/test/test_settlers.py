import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from .. import settlers, builders
from ... import monsters
from ...math import Point, Size
from .._base import RNG
from .. import _base as pcg

class MockSettler(settlers.Settler):
	def _populate(self):
		self.monsters.append(('monster', settlers.Behavior.DUMMY, Point(1, 2)))

class TestSettler(unittest.TestCase):
	def should_populate_dungeon(self):
		rng = RNG(0)
		settler = MockSettler(rng, Size(20, 20))
		settler.populate()
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
		builder = builders.RogueDungeon(rng, Size(80, 25))
		builder.build()
		self._make_terrain(builder)

		rng = RNG(0)
		settler = settlers.Squatters(rng, builder)

		self.assertTrue(settler.is_passable(Point(8, 2)))
		self.assertFalse(settler.is_passable(Point(1, 1)))
		self.assertFalse(settler.is_passable(Point(8, 1)))

		settler.monster_cells = set([Point(7, 3)])
		self.assertTrue(settler.is_free(Point(8, 2)))
		self.assertFalse(settler.is_free(Point(1, 1)))
		self.assertFalse(settler.is_free(Point(8, 1)))
		self.assertFalse(settler.is_free(next(iter(settler.monster_cells))))
		self.assertFalse(settler.is_free(builder.start_pos))
		self.assertFalse(settler.is_free(builder.exit_pos))
	def should_populate_dungeon_with_squatters(self):
		rng = RNG(0)
		builder = builders.RogueDungeon(rng, Size(80, 25))
		builder.build()
		self._make_terrain(builder)

		rng = RNG(0)
		class _MockSquatters(settlers.Squatters):
			MONSTERS = [
					('plant', monsters.Behavior.DUMMY),
					('slime', monsters.Behavior.INERT),
					('rodent', monsters.Behavior.ANGRY),
					]
			ITEMS = [
					('healing potion',),
					]
		settler = _MockSquatters(rng, builder)
		settler.populate()
		self.maxDiff = None
		self.assertEqual(settler.monsters, [
			('plant',  monsters.Behavior.DUMMY, Point(29, 20)),
			('slime',  monsters.Behavior.INERT, Point(64, 11)),
			('plant',  monsters.Behavior.DUMMY, Point(59, 4)),
			('slime',  monsters.Behavior.INERT, Point(44, 12)),
			('slime',  monsters.Behavior.INERT, Point(71, 13)),
			('slime',  monsters.Behavior.INERT, Point(36, 7)),
			('rodent', monsters.Behavior.ANGRY, Point(27, 18)),
			])
		self.assertEqual(settler.items, [
			('healing potion', Point(35, 21)),
			('healing potion', Point(63, 7)),
			])
	def should_populate_dungeon_with_weighted_squatters(self):
		rng = RNG(0)
		builder = builders.RogueDungeon(rng, Size(80, 25))
		builder.build()
		self._make_terrain(builder)

		rng = RNG(0)
		class _MockSquatters(settlers.WeightedSquatters):
			MONSTERS = [
					(1, 'plant', monsters.Behavior.DUMMY),
					(5, 'slime', monsters.Behavior.INERT),
					(10, 'rodent', monsters.Behavior.ANGRY),
					]
			ITEMS = [
					(1, 'healing potion',),
					]
		settler = _MockSquatters(rng, builder)
		settler.populate()
		self.maxDiff = None
		self.assertEqual(settler.monsters, [
			('slime',  monsters.Behavior.INERT, Point(29, 20)),
			('rodent', monsters.Behavior.ANGRY, Point(64, 11)),
			('plant',  monsters.Behavior.DUMMY, Point(59, 4)),
			('rodent', monsters.Behavior.ANGRY, Point(44, 12)),
			('rodent', monsters.Behavior.ANGRY, Point(71, 13)),
			('rodent', monsters.Behavior.ANGRY, Point(36, 7)),
			('rodent', monsters.Behavior.ANGRY, Point(27, 18)),
			])
		self.assertEqual(settler.items, [
			('healing potion', Point(35, 21)),
			('healing potion', Point(17, 11)),
			])
