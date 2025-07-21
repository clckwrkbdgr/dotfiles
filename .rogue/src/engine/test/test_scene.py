from clckwrkbdgr import unittest
from .. import scene
from clckwrkbdgr.math import Matrix, Point, Rect
from .. import terrain, actors, items, appliances
from ..mock import *

class TestActors(unittest.TestCase):
	def should_str_cells(self):
		scene = MockScene()
		self.assertEqual(scene.str_cell((0, 0)), '#')
		self.assertEqual(scene.str_cell((1, 1)), '.')
		self.assertEqual(scene.str_cell((5, 5)), '+')
		self.assertEqual(scene.str_cell((5, 6)), '*')
		self.assertEqual(scene.str_cell((6, 5)), 'g')
	def should_str_scene(self):
		scene = MockScene()
		self.assertEqual(scene.tostring(Rect((0, 0), scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#........#
				#........#
				#........#
				#....+g..#
				#....*...#
				#........#
				#........#
				##########
				"""))
	def should_str_only_part_of_scene(self):
		scene = MockScene()
		self.assertEqual(scene.tostring(Rect((3, 3), (7, 4))), unittest.dedent("""\
				......#
				......#
				..+g..#
				..*...#
				"""))
