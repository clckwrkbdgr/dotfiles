from clckwrkbdgr import unittest
from .. import scene
from clckwrkbdgr.math import Matrix, Point, Rect, Size
from clckwrkbdgr.pcg import RNG
from .. import terrain, actors, items, appliances
from ..mock import *

class TestScene(unittest.TestCase):
	def _generate(self):
		rng = RNG(0)
		builder = DungeonFloor(rng, Size(10, 10))
		builder.map_key(**({
			'exit':lambda: 'exit',
			}))
		builder.map_key(
				butterfly = lambda pos, color: Butterfly(pos, color=color),
				note = lambda text: ScribbledNote(text),
				)
		builder.generate()
		scene = Dungeon()
		scene.cells = builder.make_grid()
		scene.appliances = list(_ for _ in builder.make_appliances() if _ not in ('start', 'exit'))
		scene.monsters = list(builder.make_actors())
		scene.items = list(builder.make_items())
		return scene
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
				#........#
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
