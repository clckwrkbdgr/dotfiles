from clckwrkbdgr import unittest
from clckwrkbdgr.math import Point
from .. import actors

class MockMonster(actors.Monster):
	_sprite = '@'
	_name = 'rogue'

class TestActors(unittest.TestCase):
	def should_str_actor(self):
		rogue = MockMonster(Point(1, 1))
		self.assertEqual(str(rogue), 'rogue')
		self.assertEqual(repr(rogue), 'MockMonster(rogue @[1, 1])')
