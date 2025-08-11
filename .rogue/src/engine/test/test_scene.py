from clckwrkbdgr import unittest
from .. import scene
from clckwrkbdgr.math import Matrix, Point, Rect, Size
from clckwrkbdgr.pcg import RNG
from .. import terrain, actors, items, appliances
from ..mock import *

class TestScene(unittest.TestCase):
	def _generate(self):
		game = NanoDungeon(RNG(0))
		game.generate()
		return game.scene
	def should_str_cells(self):
		scene = self._generate()
		self.assertEqual(scene.str_cell((0, 0)), '#')
		self.assertEqual(scene.str_cell((1, 1)), '.')
		self.assertEqual(scene.str_cell((3, 2)), '&')
		self.assertEqual(scene.str_cell((1, 2)), '?')
		self.assertEqual(scene.str_cell((3, 8)), 'b')
	def should_str_scene(self):
		scene = self._generate()
		self.assertEqual(scene.tostring(Rect((0, 0), scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#........#
				##.~.....#
				#...@....#
				#..b.....#
				##########
				"""))
	def should_str_only_part_of_scene(self):
		scene = self._generate()
		self.assertEqual(scene.tostring(Rect((0, 2), (4, 8))), unittest.dedent("""\
				#?.&
				#...
				#...
				#...
				##.~
				#...
				#..b
				####
				"""))
	def should_get_terrain(self):
		scene = self._generate()
		self.assertEqual(scene.cell((0, 0)).sprite.sprite, '#')
	def should_check_validity(self):
		scene = self._generate()
		self.assertTrue(scene.valid((0, 0)))
		self.assertFalse(scene.valid((-1, -1)))
		self.assertFalse(scene.valid((scene.cells.width, scene.cells.height)))
	def should_check_passability(self):
		scene = self._generate()
		self.assertFalse(scene.is_passable((0, 0))) # '#'
		self.assertTrue(scene.is_passable((1, 1))) # '.'
		self.assertFalse(scene.is_passable((3, 2))) # '&'
		self.assertTrue(scene.is_passable((1, 2))) # '?'
		self.assertFalse(scene.is_passable((3, 8))) # 'b'
