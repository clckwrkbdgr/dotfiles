from clckwrkbdgr.math import Point, Size, Matrix, Rect
from clckwrkbdgr import unittest
from clckwrkbdgr.collections import dotdict
from ..dungeon import Scene
from ..builders import EndlessFloor, EndlessWall
from ...engine import mock

class MockScene(Scene):
	BLOCK_SIZE = Size(3, 3)
	BUILDERS = str # Dummy.
	def __init__(self, builder):
		super(MockScene, self).__init__()
		self.builder = builder

def make_scene(scene_id):
	if True:
		if scene_id == 1:
			return MockScene(MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]]))
		if scene_id == 3:
			return MockScene(MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]] + [[]]*4 + [[(2, 2)]]))

class MockBuilder(object):
	def __init__(self, rogue_pos=None, walls=None):
		self.rogue_pos = rogue_pos or (0, 0)
		self.walls = walls or []
	def build_block(self, block):
		block.clear(EndlessFloor())
		if not self.walls:
			return
		walls = self.walls.pop(0)
		for wall in walls:
			block.set_cell(wall, EndlessWall())
	def place_rogue(self, terrain):
		return self.rogue_pos

class TestDungeon(unittest.TestCase):
	VIEW_RECT = Rect((-4, -4), (9, 9))
	def should_generate_random_dungeon(self):
		scene = make_scene(1)
		scene.generate(1)
		self.assertEqual(scene.terrain.cell((0, 0)).sprite.sprite, '.')
		self.assertEqual(scene.terrain.cell((1, 0)).sprite.sprite, '#')
		self.assertEqual(scene.terrain.cell((0, 1)).sprite.sprite, '#')
		self.assertEqual(scene.terrain.cell((1, 1)).sprite.sprite, '.')
		self.assertEqual(scene._player_pos, (1, 1))

		player = mock.Rogue(None)
		scene.enter_actor(player, None)
		self.assertEqual(list(scene.iter_active_monsters()), [player])
	def should_recalibrate_plane_after_player_moved(self):
		scene = make_scene(3)
		scene.generate(3)
		scene.enter_actor(mock.Rogue(None), None)

		self.assertEqual(scene.get_player().pos, (1, 1))
		self.assertEqual(scene.terrain.shift, Point(-3, -3))
		self.assertEqual(scene.tostring(self.VIEW_RECT), unittest.dedent("""\
		_________
		_........
		_........
		_........
		_....#...
		_...#@...
		_........
		_........
		_........
		""").replace('_', ' '))

		scene.get_player().pos = Point(1, 2)
		scene.recalibrate(scene.get_player().pos)
		self.assertEqual(scene.terrain.shift, Point(-3, -3))
		self.assertEqual(scene.tostring(self.VIEW_RECT), unittest.dedent("""\
		_________
		_........
		_........
		_........
		_....#...
		_...#....
		_....@...
		_........
		_........
		""").replace('_', ' '))

		scene.get_player().pos = Point(1, 3)
		scene.recalibrate(scene.get_player().pos)
		self.assertEqual(scene.terrain.shift, Point(-3, 0))
		self.assertEqual(scene.tostring(self.VIEW_RECT), unittest.dedent("""\
		_________
		_________
		_________
		_________
		_....#...
		_...#....
		_........
		_....@...
		_........
		""").replace('_', ' '))
