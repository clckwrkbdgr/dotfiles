from clckwrkbdgr import unittest
from clckwrkbdgr.math import Point
from .. import math

class TestMovement(unittest.TestCase):
	def should_detect_diagonal_movement(self):
		self.assertTrue(math.is_diagonal(Point(0, 0) - Point(1, 1)))
		self.assertTrue(math.is_diagonal(Point(0, 0) - Point(-1, 1)))
		self.assertTrue(math.is_diagonal(Point(0, 0) - Point(1, -1)))
		self.assertTrue(math.is_diagonal(Point(0, 0) - Point(-1, -1)))
		self.assertTrue(math.is_diagonal(Point(1, 1) - Point(2, 0)))

		self.assertFalse(math.is_diagonal(Point(0, 0) - Point(1, 0)))
		self.assertFalse(math.is_diagonal(Point(0, 0) - Point(0, 1)))
		self.assertFalse(math.is_diagonal(Point(0, 0) - Point(-1, 0)))
		self.assertFalse(math.is_diagonal(Point(0, 0) - Point(0, -1)))
		self.assertFalse(math.is_diagonal(Point(0, 0) - Point(2, 2)))
