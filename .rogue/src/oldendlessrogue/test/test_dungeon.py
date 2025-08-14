from clckwrkbdgr.math import Point, Size, Matrix, Rect
from clckwrkbdgr import unittest
from clckwrkbdgr.collections import dotdict
from ..dungeon import Dungeon, Scene
from ..builders import EndlessFloor, EndlessWall
from ...engine import mock

class MockScene(Scene):
	BLOCK_SIZE = Size(3, 3)

class MockDungeon(Dungeon):
	PLAYER_TYPE = mock.Rogue

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

class MockBuilder_1(MockBuilder):
	def __init__(self):
		super(MockBuilder_1, self).__init__(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
class MockScene_1(MockScene):
	BUILDERS = MockBuilder_1
class MockDungeon_1(MockDungeon):
	def get_scene_class(self): return MockScene_1
class MockBuilder_2(MockBuilder):
	def __init__(self):
		super(MockBuilder_2, self).__init__(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0)]])
class MockScene_2(MockScene):
	BUILDERS = MockBuilder_2
class MockDungeon_2(MockDungeon):
	def get_scene_class(self): return MockScene_2
class MockBuilder_3(MockBuilder):
	def __init__(self):
		super(MockBuilder_3, self).__init__(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]] + [[]]*4 + [[(2, 2)]])
class MockScene_3(MockScene):
	BUILDERS = MockBuilder_3
class MockDungeon_3(MockDungeon):
	def get_scene_class(self): return MockScene_3

class TestDungeon(unittest.TestCase):
	VIEW_RECT = Rect((-4, -4), (9, 9))
	def should_generate_random_dungeon(self):
		dungeon = MockDungeon_1()
		dungeon.generate(1)
		self.assertEqual(dungeon.scene.terrain.cell((0, 0)).sprite.sprite, '.')
		self.assertEqual(dungeon.scene.terrain.cell((1, 0)).sprite.sprite, '#')
		self.assertEqual(dungeon.scene.terrain.cell((0, 1)).sprite.sprite, '#')
		self.assertEqual(dungeon.scene.terrain.cell((1, 1)).sprite.sprite, '.')
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
	def should_move_player(self):
		dungeon = MockDungeon_1()
		dungeon.generate(1)
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
		dungeon.move_actor(dungeon.scene.get_player(), Point(0, 1))
		dungeon.process_others()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 2))
	def should_not_move_player_into_wall(self):
		dungeon = MockDungeon_2()
		dungeon.generate(2)
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
		dungeon.move_actor(dungeon.scene.get_player(), Point(0, -1))
		dungeon.process_others()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
	def should_recalibrate_plane_after_player_moved(self):
		dungeon = MockDungeon_3()
		dungeon.generate(3)
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
		self.assertEqual(dungeon.scene.terrain.shift, Point(-3, -3))
		self.assertEqual(dungeon.scene.tostring(self.VIEW_RECT), unittest.dedent("""\
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

		dungeon.move_actor(dungeon.scene.get_player(), Point(0, 1))
		dungeon.process_others()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 2))
		self.assertEqual(dungeon.scene.terrain.shift, Point(-3, -3))
		self.assertEqual(dungeon.scene.tostring(self.VIEW_RECT), unittest.dedent("""\
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

		dungeon.move_actor(dungeon.scene.get_player(), Point(0, 1))
		dungeon.process_others()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 3))
		self.assertEqual(dungeon.scene.terrain.shift, Point(-3, 0))
		self.assertEqual(dungeon.scene.tostring(self.VIEW_RECT), unittest.dedent("""\
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

class TestSerialization(unittest.TestCase):
	def should_serialize_deserialize_dungeon(self):
		dungeon = MockDungeon_1()
		dungeon.generate(1)
		dungeon.playing_time = 666

		import pickle
		from clckwrkbdgr.collections import dotdict
		data = dotdict()
		dungeon.save(data)
		other_data = pickle.loads(pickle.dumps(data))
		other = MockDungeon_1()
		other.load(other_data)
		self.maxDiff = None
		self.assertEqual(
				'\n'.join(dungeon.scene.terrain.blocks.cell(c).tostring(lambda x:x.sprite.sprite) for c in dungeon.scene.terrain.blocks),
				'\n'.join(other.scene.terrain.blocks.cell(c).tostring(lambda x:x.sprite.sprite) for c in other.scene.terrain.blocks),
				)
		self.assertEqual(dungeon.scene.get_player().pos, other.scene.get_player().pos)
		self.assertEqual(dungeon.playing_time, other.playing_time)
	def should_deserialize_dungeons_from_previous_versions(self):
		dungeon = MockDungeon_1()
		dungeon.generate(1)

		state = {'scene': dotdict({'terrain':dungeon.scene.terrain, 'rogue':dungeon.scene.get_player()})}
		other = MockDungeon_1()
		other.load(state)
		self.assertEqual(other.playing_time, 0)
