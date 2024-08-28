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
		from ...game import Cell, Game, Terrain # FIXME circular dependency
		class MockRogueDungeon(Game):
			TERRAIN = {
				None : Terrain(' ', False),
				'corner' : Terrain("+", False, remembered='+'),
				'rogue_door' : Terrain("+", True, remembered='+', allow_diagonal=False, dark=True),
				'floor' : Terrain(".", True),
				'rogue_passage' : Terrain("#", True, remembered='#', allow_diagonal=False, dark=True),
				'wall_h' : Terrain("-", False, remembered='-'),
				'wall_v' : Terrain("|", False, remembered='|'),
				}
		for pos in builder.strata.size:
			builder.strata.set_cell(
					pos.x, pos.y,
					Cell(MockRogueDungeon.TERRAIN[builder.strata.cell(pos.x, pos.y)]),
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
			('plant',  monsters.Behavior.DUMMY, Point(x=29, y=20)),
			('slime',  monsters.Behavior.INERT, Point(x=64, y=11)),
			('plant',  monsters.Behavior.DUMMY, Point(x=59, y=4)),
			('slime',  monsters.Behavior.INERT, Point(x=44, y=12)),
			('slime',  monsters.Behavior.INERT, Point(x=71, y=13)),
			('slime',  monsters.Behavior.INERT, Point(x=36, y=7)),
			('rodent', monsters.Behavior.ANGRY, Point(x=27, y=18)),
			])
		self.assertEqual(settler.items, [
			('healing potion', Point(x=35, y=21)),
			('healing potion', Point(x=63, y=7)),
			])
