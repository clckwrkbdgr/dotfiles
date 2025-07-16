from clckwrkbdgr.math import Point, Size, Matrix
from clckwrkbdgr import unittest
from clckwrkbdgr.collections import dotdict
from ..dungeon import Dungeon, Scene

class MockScene(Scene):
	BLOCK_SIZE = Size(3, 3)

class MockDungeon(Dungeon):
	def __init__(self, *args, **kwargs):
		super(MockDungeon, self).__init__(*args, **kwargs)
		self.scene = MockScene()

class MockBuilder:
	def __init__(self, rogue_pos=None, walls=None):
		self.rogue_pos = rogue_pos or (0, 0)
		self.walls = walls or []
	def build_block(self, block):
		block.clear('.')
		if not self.walls:
			return
		walls = self.walls.pop(0)
		for wall in walls:
			block.set_cell(wall, '#')
	def place_rogue(self, terrain):
		return self.rogue_pos

class TestDungeon(unittest.TestCase):
	@staticmethod
	def to_string(dungeon):
		result = []
		for y in range(-4, 5):
			result.append('')
			for x in range(-4, 5):
				result[-1] += (dungeon.get_sprite((x, y)) or ' ')
		return '\n'.join(result) + '\n'
	def should_generate_random_dungeon(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.scene.terrain.cell((0, 0)), '.')
		self.assertEqual(dungeon.scene.terrain.cell((1, 0)), '#')
		self.assertEqual(dungeon.scene.terrain.cell((0, 1)), '#')
		self.assertEqual(dungeon.scene.terrain.cell((1, 1)), '.')
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
	def should_get_dungeon_sprites_for_view(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.get_sprite((0, 0)), '.')
		self.assertEqual(dungeon.get_sprite((1, 1)), '@')
		self.assertEqual(dungeon.get_sprite((0, 1)), '#')
		self.assertEqual(dungeon.get_sprite((1, 0)), '#')
	def should_move_player(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
		dungeon.shift_monster(dungeon.scene.get_player(), Point(0, 1))
		dungeon.finish_action()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 2))
	def should_not_move_player_into_wall(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
		dungeon.shift_monster(dungeon.scene.get_player(), Point(0, -1))
		dungeon.finish_action()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
	def should_recalibrate_plane_after_player_moved(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]] + [[]]*4 + [[(2, 2)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 1))
		self.assertEqual(dungeon.scene.terrain.shift, Point(-3, -3))
		self.assertEqual(self.to_string(dungeon), unittest.dedent("""\
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

		dungeon.shift_monster(dungeon.scene.get_player(), Point(0, 1))
		dungeon.finish_action()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 2))
		self.assertEqual(dungeon.scene.terrain.shift, Point(-3, -3))
		self.assertEqual(self.to_string(dungeon), unittest.dedent("""\
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

		dungeon.shift_monster(dungeon.scene.get_player(), Point(0, 1))
		dungeon.finish_action()
		self.assertEqual(dungeon.scene.get_player().pos, (1, 3))
		self.assertEqual(dungeon.scene.terrain.shift, Point(-3, 0))
		self.assertEqual(self.to_string(dungeon), unittest.dedent("""\
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
	def should_check_if_cell_is_passable(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.scene.terrain.cell((0, 0)), '.')
		self.assertTrue(dungeon.scene.is_passable((0, 0)))
		self.assertFalse(dungeon.scene.is_passable((1, 0)))
		self.assertFalse(dungeon.scene.is_passable((-10, -10)))

class TestSerialization(unittest.TestCase):
	def should_serialize_deserialize_dungeon(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		dungeon.time = 666

		import pickle
		from clckwrkbdgr.collections import dotdict
		data = dotdict()
		dungeon.save(data)
		other_data = pickle.loads(pickle.dumps(data))
		other = MockDungeon(builder=builder)
		other.load(other_data)
		self.assertEqual(dungeon.scene.terrain, other.scene.terrain)
		self.assertEqual(dungeon.scene.get_player().pos, other.scene.get_player().pos)
		self.assertEqual(dungeon.time, other.time)
	def should_deserialize_dungeons_from_previous_versions(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()

		state = {'builder' : builder, 'scene': dotdict({'terrain':dungeon.scene.terrain, 'rogue':dungeon.scene.get_player()})}
		other = MockDungeon(builder=builder)
		other.load(state)
		self.assertEqual(other.time, 0)
