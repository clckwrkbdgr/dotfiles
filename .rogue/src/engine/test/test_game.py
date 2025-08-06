from clckwrkbdgr import unittest
from .. import _base
from .. import events
from ..mock import *

class TestUtils(unittest.TestCase):
	def should_detect_diagonal_movement(self):
		self.assertTrue(_base.is_diagonal(Point(0, 0) - Point(1, 1)))
		self.assertTrue(_base.is_diagonal(Point(0, 0) - Point(-1, 1)))
		self.assertTrue(_base.is_diagonal(Point(0, 0) - Point(1, -1)))
		self.assertTrue(_base.is_diagonal(Point(0, 0) - Point(-1, -1)))
		self.assertTrue(_base.is_diagonal(Point(1, 1) - Point(2, 0)))

		self.assertFalse(_base.is_diagonal(Point(0, 0) - Point(1, 0)))
		self.assertFalse(_base.is_diagonal(Point(0, 0) - Point(0, 1)))
		self.assertFalse(_base.is_diagonal(Point(0, 0) - Point(-1, 0)))
		self.assertFalse(_base.is_diagonal(Point(0, 0) - Point(0, -1)))
		self.assertFalse(_base.is_diagonal(Point(0, 0) - Point(2, 2)))

class TestEvents(unittest.TestCase):
	def should_process_events(self):
		game = _base.Game()
		game.fire_event(DropItem(who='me', where='floor', what='something'))
		self.assertEqual(list(game.process_events()), [
			'me drops something on floor',
			])
