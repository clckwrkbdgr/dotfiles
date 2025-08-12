from clckwrkbdgr import unittest
import textwrap
from clckwrkbdgr.math import Point, Matrix
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

class MockScene(object):
	def __init__(self, grid):
		self.grid = Matrix.fromstring(grid)
	def valid(self, pos):
		return self.grid.valid(pos)
	def cell(self, pos):
		return self.grid.cell(pos)
	def is_passable(self, pos):
		return self.cell(pos) in ['.', '~']
	def allow_movement_direction(self, from_point, to_point):
		if not math.is_diagonal(to_point - from_point):
			return True
		if self.cell(from_point) == '~':
			return False
		if self.cell(to_point) == '~':
			return False
		return True

class MockVision(object):
	def __init__(self, grid):
		self.grid = Matrix.fromstring(grid)
	def is_explored(self, pos):
		return self.grid.cell(pos) == '*'

class TestPathfinder(unittest.TestCase):
	def should_place_path(self):
		scene = MockScene(textwrap.dedent("""\
				#############
				#~#~~.......#
				#~~~#.###.#.#
				#~###.....#.#
				#############
				"""))
		vision = MockVision(textwrap.dedent("""\
				*************
				******~~~****
				*************
				*************
				*************
				"""))
		wave = math.Pathfinder(scene, vision=vision)

		self.assertFalse(wave.is_frontier(Point(4, 1)))
		self.assertTrue(wave.is_frontier(Point(5, 1)))

		start = Point(1, 1)
		dest = Point(11, 3)
		path = wave.run(start, lambda wave: dest if dest in wave else None)

		for pos in path:
			scene.grid.set_cell(pos, '*')
		expected = textwrap.dedent("""\
				#############
				#*#***....*.#
				#***#*###*#*#
				#~###.***.#*#
				#############
				""")
		self.assertEqual(scene.grid.tostring(), expected)
