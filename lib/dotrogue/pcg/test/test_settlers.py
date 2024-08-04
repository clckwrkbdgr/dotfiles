import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from .. import settlers
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
