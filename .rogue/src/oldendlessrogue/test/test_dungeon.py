from clckwrkbdgr.math import Point, Size, Matrix
from clckwrkbdgr import unittest
from ..dungeon import Dungeon

class MockDungeon(Dungeon):
	BLOCK_SIZE = Size(3, 3)

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
		self.assertEqual(dungeon.terrain.cell((0, 0)), '.')
		self.assertEqual(dungeon.terrain.cell((1, 0)), '#')
		self.assertEqual(dungeon.terrain.cell((0, 1)), '#')
		self.assertEqual(dungeon.terrain.cell((1, 1)), '.')
		self.assertEqual(dungeon.rogue, (1, 1))
	def should_get_dungeon_sprites_for_view(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.get_sprite((-1, -1)), '.')
		self.assertEqual(dungeon.get_sprite((0, 0)), '@')
		self.assertEqual(dungeon.get_sprite((-1, 0)), '#')
		self.assertEqual(dungeon.get_sprite((0, -1)), '#')
	def should_move_player(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.rogue, (1, 1))
		dungeon.control(Point(0, 1))
		self.assertEqual(dungeon.rogue, (1, 2))
	def should_not_move_player_into_wall(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.rogue, (1, 1))
		dungeon.control(Point(0, -1))
		self.assertEqual(dungeon.rogue, (1, 1))
	def should_recalibrate_plane_after_player_moved(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]] + [[]]*4 + [[(2, 2)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.rogue, (1, 1))
		self.assertEqual(dungeon.terrain.shift, Point(-3, -3))
		self.assertEqual(self.to_string(dungeon), unittest.dedent("""\
		.........
		.........
		.........
		....#....
		...#@....
		.........
		.........
		.........
		.........
		"""))

		dungeon.control(Point(0, 1))
		self.assertEqual(dungeon.rogue, (1, 2))
		self.assertEqual(dungeon.terrain.shift, Point(-3, -3))
		self.assertEqual(self.to_string(dungeon), unittest.dedent("""\
		.........
		.........
		....#....
		...#.....
		....@....
		.........
		.........
		.........
		""") + ' '*9 + '\n')

		dungeon.control(Point(0, 1))
		self.assertEqual(dungeon.rogue, (1, 3))
		self.assertEqual(dungeon.terrain.shift, Point(-3, 0))
		self.assertEqual(self.to_string(dungeon), ' '*9 + '\n' + unittest.dedent("""\
		....#....
		...#.....
		.........
		....@....
		.........
		.........
		.........
		.........
		"""))
	def should_check_if_cell_is_passable(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		self.assertEqual(dungeon.terrain.cell((0, 0)), '.')
		self.assertTrue(dungeon.is_passable((0, 0)))
		self.assertFalse(dungeon.is_passable((1, 0)))
		self.assertFalse(dungeon.is_passable((-10, -10)))
	def should_raise_given_game_exception(self):
		builder = MockBuilder(rogue_pos=(1, 1))
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()
		class MockEvent(Exception): pass
		with self.assertRaises(MockEvent):
			dungeon.control(MockEvent)
		with self.assertRaises(MockEvent):
			dungeon.control(MockEvent())

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
		self.assertEqual(dungeon.terrain, other.terrain)
		self.assertEqual(dungeon.rogue, other.rogue)
		self.assertEqual(dungeon.time, other.time)
	def should_deserialize_dungeons_from_previous_versions(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.generate()

		state = {'builder' : builder, 'terrain':dungeon.terrain, 'rogue':dungeon.rogue}
		other = MockDungeon(builder=builder)
		other.load(state)
		self.assertEqual(other.time, 0)
