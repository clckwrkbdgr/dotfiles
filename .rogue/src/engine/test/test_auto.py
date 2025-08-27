from clckwrkbdgr import unittest
from .. import auto
from ..mock import *

class TestAutoMode(unittest.TestCase):
	def should_auto_walk_to_position(self):
		dungeon = NanoDungeon()
		dungeon.generate(None)
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 5))

		self.assertFalse(dungeon.perform_automovement())
		dungeon.automove(Point(2, 3))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		self.assertFalse(dungeon.perform_automovement()) # You have reached your destination.

		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), unittest.dedent("""\
				_        _
				#....    _
				#?.&.    _
				#.@..    _
				#....    _
				#<...    _
				##  >    _
				#        _
				_        _
				_        _
				""").replace('_', ' '))
