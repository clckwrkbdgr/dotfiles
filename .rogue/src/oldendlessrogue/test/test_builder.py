from clckwrkbdgr.math import Point, Size, Matrix
from clckwrkbdgr import unittest
from ..dungeon import EndlessMatrix as Strata
from ..builders import *

class MockBuilder:
	def build_block(self, block):
		pass

class TestMainBuilder(unittest.TestCase):
	@unittest.mock.patch('random.choice', side_effect=['fill_with_garbage'])
	@unittest.mock.patch('random.randrange', side_effect=[0, 1, 1, 0, 2, 2])
	def should_build_block(self, random_randrange, random_choice):
		block = Matrix((3, 3), '.')
		builder = Builders()
		builder.build_block(block)
		self.assertEqual(block.tostring(), '.#.\n#..\n..#\n')
	def should_place_rogue(self):
		terrain = Strata(block_size=(3, 3), builder=MockBuilder().build_block)
		builder = Builders()
		pos = builder.place_rogue(terrain)
		self.assertEqual(pos, (1, 1))

class TestBuildings(unittest.TestCase):
	def should_create_square_tank(self):
		field = Matrix((6, 6), '.')
		place_square_tank(field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(), unittest.dedent("""\
		......
		.####.
		.####.
		.####.
		.####.
		......
		"""))
	def should_create_round_tank(self):
		field = Matrix((6, 6), '.')
		place_round_tank(field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(), unittest.dedent("""\
		......
		..##..
		.####.
		.####.
		..##..
		......
		"""))
	@unittest.mock.patch('random.choice', side_effect=[False, True, False, True,
													 True, True, False, False,
													 False, False, True, False,
													 True, False, False, True,
													 ])
	def should_create_broken_tank(self, random_choice):
		field = Matrix((6, 6), '.')
		place_broken_tank(field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(), unittest.dedent("""\
		......
		..#.#.
		.##...
		...#..
		.#..#.
		......
		"""))

class TestBuilders(unittest.TestCase):
	@unittest.mock.patch('random.randrange', side_effect=[0, 1, 1, 0, 2, 2])
	def should_fill_block_with_garbage(self, random_randrange):
		field = Matrix((3, 3), '.')
		fill_with_garbage(field)
		self.assertEqual(field.tostring(), '.#.\n#..\n..#\n')
	@unittest.mock.patch('random.randrange', side_effect=[1, 1])
	def should_build_empty_square(self, random_randrange):
		field = Matrix((3, 3), '.')
		empty_square(field)
		self.assertEqual(field.tostring(), '...\n.#.\n...\n')
	@unittest.mock.patch('random.choice', side_effect=[place_square_tank]*4)
	@unittest.mock.patch('random.randrange', side_effect=[1, 2])
	def should_build_field_of_tanks(self, random_randrange, random_choice):
		field = Matrix((13, 13), '.')
		field_of_tanks(field)
		self.assertEqual(field.tostring(), unittest.dedent("""\
		.............
		.............
		.............
		..####.####..
		..####.####..
		..####.####..
		..####.####..
		.............
		..####.####..
		..####.####..
		..####.####..
		..####.####..
		.............
		"""))
