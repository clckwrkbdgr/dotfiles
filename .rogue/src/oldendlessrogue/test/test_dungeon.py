from clckwrkbdgr.math import Point, Size, Matrix
from clckwrkbdgr import unittest
from ..dungeon import Dungeon, Strata

class MockDungeon(Dungeon):
	BLOCK_SIZE = Size(3, 3)

class MockBuilder:
	def __init__(self, rogue_pos=None, walls=None):
		self.rogue_pos = rogue_pos or (0, 0)
		self.walls = walls or []
	def build_block(self, block):
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
				result[-1] += dungeon.get_sprite((x, y))
		return '\n'.join(result) + '\n'
	def should_generate_random_dungeon(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		self.assertEqual(dungeon.terrain.cell((0, 0)), '.')
		self.assertEqual(dungeon.terrain.cell((1, 0)), '#')
		self.assertEqual(dungeon.terrain.cell((0, 1)), '#')
		self.assertEqual(dungeon.terrain.cell((1, 1)), '.')
		self.assertEqual(dungeon.rogue, (1, 1))
	def should_get_dungeon_sprites_for_view(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		self.assertEqual(dungeon.get_sprite((-1, -1)), '.')
		self.assertEqual(dungeon.get_sprite((0, 0)), '@')
		self.assertEqual(dungeon.get_sprite((-1, 0)), '#')
		self.assertEqual(dungeon.get_sprite((0, -1)), '#')
	def should_move_player(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		self.assertEqual(dungeon.rogue, (1, 1))
		dungeon.control(Point(0, 1))
		self.assertEqual(dungeon.rogue, (1, 2))
	def should_not_move_player_into_wall(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0)]])
		dungeon = MockDungeon(builder=builder)
		self.assertEqual(dungeon.rogue, (1, 1))
		dungeon.control(Point(0, -1))
		self.assertEqual(dungeon.rogue, (1, 1))
	def should_recalibrate_plane_after_player_moved(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]] + [[]]*4 + [[(2, 2)]])
		dungeon = MockDungeon(builder=builder)
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
	def should_raise_given_game_exception(self):
		builder = MockBuilder(rogue_pos=(1, 1))
		dungeon = MockDungeon(builder=builder)
		class MockEvent(Exception): pass
		with self.assertRaises(MockEvent):
			dungeon.control(MockEvent)
		with self.assertRaises(MockEvent):
			dungeon.control(MockEvent())

class TestSerialization(unittest.TestCase):
	def should_serialize_deserialize_dungeon(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)
		dungeon.time = 666

		import pickle
		other = pickle.loads(pickle.dumps(dungeon))
		self.assertEqual(dungeon.terrain, other.terrain)
		self.assertEqual(dungeon.rogue, other.rogue)
		self.assertEqual(dungeon.time, other.time)
	def should_deserialize_dungeons_from_previous_versions(self):
		builder = MockBuilder(rogue_pos=(1, 1), walls=[[]]*4+[[(1, 0), (0, 1)]])
		dungeon = MockDungeon(builder=builder)

		state = {'terrain':dungeon.terrain, 'rogue':dungeon.rogue}
		other = object.__new__(Dungeon)
		other.__setstate__(state)
		self.assertEqual(other.time, 0)

class TestStrata(unittest.TestCase):
	@staticmethod
	def to_string(strata):
		result = []
		for y in range(strata.shift.y, strata.shift.y + strata.block_size.y * 3):
			result.append('')
			for x in range(strata.shift.x, strata.shift.x + strata.block_size.x * 3):
				result[-1] += strata.cell((x, y))
		return '\n'.join(result) + '\n'

	def setUp(self):
		self.builder = MockBuilder(walls=[
			[(0, 0)], [(1, 0)], [(2, 0)],
			[(0, 1)], [(1, 1)], [(2, 1)],
			[(0, 2)], [(1, 2)], [(2, 2)],

			[(0, 0), (1, 0), (2, 0)],
			[(0, 1), (1, 1), (2, 1)],
			[(0, 2), (1, 2), (2, 2)],

			[(0, 0), (0, 1), (0, 2)],
			[(1, 0), (1, 1), (1, 2)],
			[(2, 0), (2, 1), (2, 2)],

			[(0, 0), (1, 0), (0, 1)],
			[(0, 0), (1, 1), (2, 0)],
			[(1, 0), (2, 0), (2, 1)],
			[(0, 0), (1, 1), (0, 2)],
			[(1, 0), (0, 1), (2, 1), (1, 2)],
			[(2, 0), (1, 1), (2, 2)],
			[(0, 2), (1, 2), (0, 1)],
			[(0, 2), (1, 1), (2, 2)],
			[(1, 2), (2, 2), (2, 1)],
			])
		self.strata = Strata(block_size=(3, 3), builder=self.builder)
	def should_create_and_build_strata(self):
		self.assertEqual(self.to_string(self.strata), unittest.dedent("""\
		#...#...#
		.........
		.........
		.........
		#...#...#
		.........
		.........
		.........
		#...#...#
		"""))
	def should_check_if_cell_is_passable(self):
		self.assertTrue(self.strata.is_passable((0, 0)))
		self.assertFalse(self.strata.is_passable((1, 1)))
		self.assertFalse(self.strata.is_passable((-10, -10)))
	def should_check_if_cell_coords_are_valid(self):
		self.assertTrue(self.strata.valid((0, 0)))
		self.assertTrue(self.strata.valid((1, 1)))
		self.assertFalse(self.strata.valid((-10, -10)))
	def should_return_empty_sprite_for_cells_outside(self):
		self.assertEqual(self.strata.cell((-10, -10)), ' ')
	def should_recalibrate_layout_when_anchor_point_is_changed(self):
		original = unittest.dedent("""\
		#...#...#
		.........
		.........
		.........
		#...#...#
		.........
		.........
		.........
		#...#...#
		""")
		self.assertEqual(self.strata.shift, Point(-3, -3))
		self.assertEqual(self.to_string(self.strata), original)
		self.strata.recalibrate((0, 0))
		self.assertEqual(self.strata.shift, Point(-3, -3))
		self.assertEqual(self.to_string(self.strata), original)
		self.strata.recalibrate((1, 0))
		self.assertEqual(self.strata.shift, Point(-3, -3))
		self.assertEqual(self.to_string(self.strata), original)
		self.strata.recalibrate((2, 0))
		self.assertEqual(self.strata.shift, Point(-3, -3))
		self.assertEqual(self.to_string(self.strata), original)

		shifted_right = unittest.dedent("""\
		.#...####
		.........
		.........
		.........
		.#...####
		.........
		.........
		.........
		.#...####
		""")
		self.strata.recalibrate((3, 0))
		self.assertEqual(self.strata.shift, Point(0, -3))
		self.assertEqual(self.to_string(self.strata), shifted_right)

		shifted_left = unittest.dedent("""\
		#...#...#
		#........
		#........
		.#.......
		.#..#...#
		.#.......
		..#......
		..#......
		..#.#...#
		""")
		self.strata.recalibrate((2, 0))
		self.assertEqual(self.strata.shift, Point(-3, -3))
		self.assertEqual(self.to_string(self.strata), shifted_left)

		completely_new = unittest.dedent("""\
		##.#.#.##
		#...#...#
		.........
		#...#...#
		.#.#.#.#.
		#...#...#
		.........
		#...#...#
		##.#.#.##
		""")
		self.strata.recalibrate((20, 20))
		self.assertEqual(self.strata.shift, Point(15, 15))
		self.assertEqual(self.to_string(self.strata), completely_new)
