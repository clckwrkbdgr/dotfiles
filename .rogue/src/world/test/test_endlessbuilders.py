from clckwrkbdgr.math import Point, Size, Matrix
from clckwrkbdgr import unittest
from ..endlessbuilders import *
from ...engine import ui, terrain

class MockVoid(terrain.Terrain):
	_sprite = ui.Sprite(' ', None)
class MockFloor(terrain.Terrain):
	_sprite = ui.Sprite('.', None)
class MockWall(terrain.Terrain):
	_sprite = ui.Sprite('#', None)

class MockEndlessBuilder(object):
	class Mapping(object):
		void = MockVoid()
		floor = MockFloor()
		wall = MockWall()
		@staticmethod
		def start(): return 'start'

class MockFieldOfTanks(MockEndlessBuilder, FieldOfTanks):
	pass
class MockEmptySquare(MockEndlessBuilder, EmptySquare):
	pass
class MockFilledWithGarbage(MockEndlessBuilder, FilledWithGarbage):
	pass

class TestMainBuilder(unittest.TestCase):
	@unittest.mock.patch('random.choice', side_effect=[MockFilledWithGarbage])
	@unittest.mock.patch('random.randrange', side_effect=[0, 1, 1, 0, 2, 2])
	def should_build_block(self, random_randrange, random_choice):
		block = Matrix((3, 3), MockVoid())
		builder = Builders(utils.all_subclasses(MockEndlessBuilder))
		builder.build_block(block)
		self.assertEqual(block.tostring(lambda c: c.sprite.sprite), '.#.\n#..\n..#\n')
	def should_place_rogue(self):
		block = Matrix((3, 3), '.')
		builder = Builders(utils.all_subclasses(MockEndlessBuilder))
		builder.build_block(block)
		pos = builder._start_pos
		self.assertEqual(pos, (1, 1))

class TestBuildings(unittest.TestCase):
	def should_create_square_tank(self):
		field = Matrix((6, 6), 'floor')
		place_square_tank(field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(lambda c: '#' if c == 'wall' else '.'), unittest.dedent("""\
		......
		.####.
		.####.
		.####.
		.####.
		......
		"""))
	def should_create_round_tank(self):
		field = Matrix((6, 6), 'floor')
		place_round_tank(field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(lambda c: '#' if c == 'wall' else '.'), unittest.dedent("""\
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
		field = Matrix((6, 6), 'floor')
		place_broken_tank(field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(lambda c: '#' if c == 'wall' else '.'), unittest.dedent("""\
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
		builder = FilledWithGarbage(random, field)
		builder.generate()
		builder.map_key(floor=MockFloor())
		builder.map_key(wall=MockWall())
		builder.make_grid()
		self.assertEqual(field.tostring(lambda c: c.sprite.sprite), '.#.\n#..\n..#\n')
	@unittest.mock.patch('random.randrange', side_effect=[1, 1])
	def should_build_empty_square(self, random_randrange):
		field = Matrix((3, 3), '.')
		builder = EmptySquare(random, field)
		builder.generate()
		builder.map_key(floor=MockFloor())
		builder.map_key(wall=MockWall())
		builder.make_grid()
		self.assertEqual(field.tostring(lambda c: c.sprite.sprite), '...\n.#.\n...\n')
	@unittest.mock.patch('random.choice', side_effect=[place_square_tank]*4)
	@unittest.mock.patch('random.randrange', side_effect=[1, 2])
	def should_build_field_of_tanks(self, random_randrange, random_choice):
		field = Matrix((13, 13), '.')
		builder = FieldOfTanks(random, field)
		builder.generate()
		builder.map_key(floor=MockFloor())
		builder.map_key(wall=MockWall())
		builder.make_grid()
		self.assertEqual(field.tostring(lambda c: c.sprite.sprite), unittest.dedent("""\
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
