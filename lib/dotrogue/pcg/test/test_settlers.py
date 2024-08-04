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
	def should_populate_dungeon_with_squatters(self):
		rng = RNG(0)
		builder = builders.RogueDungeon(rng, Size(80, 25))
		builder.build()
		from ...game import Cell, Game # FIXME circular dependency
		for pos in builder.strata.size:
			builder.strata.set_cell(
					pos.x, pos.y,
					Cell(Game.TERRAIN[builder.strata.cell(pos.x, pos.y)]),
					)

		rng = RNG(0)
		settler = settlers.Squatters(rng, builder)
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
