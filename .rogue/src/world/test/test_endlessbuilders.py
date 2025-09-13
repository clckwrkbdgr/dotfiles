from clckwrkbdgr.math import Point, Size, Matrix
from clckwrkbdgr import unittest
from ..endlessbuilders import *
from ...engine import ui, terrain
from ...engine.mock import *

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
		@staticmethod
		def overworld_exit(): return StairsUp('overworld', None)

class MockFieldOfTanks(MockEndlessBuilder, FieldOfTanks):
	pass
class MockEmptySquare(MockEndlessBuilder, EmptySquare):
	pass
class MockFilledWithGarbage(MockEndlessBuilder, FilledWithGarbage):
	pass

class TestMainBuilder(unittest.TestCase):
	def should_build_block(self):
		block = Matrix((3, 3), MockVoid())
		builder = Builders(utils.all_subclasses(MockEndlessBuilder), rng=RNG(1))
		builder.build_block(block)
		self.assertEqual(block.tostring(lambda c: c.sprite.sprite), '#..\n...\n...\n')
	def should_place_rogue(self):
		block = Matrix((3, 3), '.')
		builder = Builders(utils.all_subclasses(MockEndlessBuilder), rng=RNG(0))
		builder.build_block(block)
		pos = builder._start_pos
		self.assertEqual(pos, (2, 0))

class TestBuildings(unittest.TestCase):
	def should_create_square_tank(self):
		field = Matrix((6, 6), 'floor')
		place_square_tank(RNG(0), field, (1, 1), (4, 4))
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
		place_round_tank(RNG(0), field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(lambda c: '#' if c == 'wall' else '.'), unittest.dedent("""\
		......
		..##..
		.####.
		.####.
		..##..
		......
		"""))
	def should_create_broken_tank(self):
		field = Matrix((6, 6), 'floor')
		place_broken_tank(RNG(0), field, (1, 1), (4, 4))
		self.assertEqual(field.tostring(lambda c: '#' if c == 'wall' else '.'), unittest.dedent("""\
		......
		......
		.##...
		....#.
		.####.
		......
		"""))

class TestBuilders(unittest.TestCase):
	def should_fill_block_with_garbage(self):
		field = Matrix((3, 3), '.')
		builder = FilledWithGarbage(RNG(0), field)
		builder.generate()
		builder.map_key(floor=MockFloor())
		builder.map_key(wall=MockWall())
		builder.make_grid()
		self.assertEqual(field.tostring(lambda c: c.sprite.sprite), '...\n#..\n#..\n')
	def should_build_empty_square(self):
		field = Matrix((3, 3), '.')
		builder = EmptySquare(RNG(0), field)
		builder.generate()
		builder.map_key(floor=MockFloor())
		builder.map_key(wall=MockWall())
		builder.make_grid()
		self.assertEqual(field.tostring(lambda c: c.sprite.sprite), '...\n#..\n...\n')
	def should_build_field_of_tanks(self):
		field = Matrix((13, 13), '.')
		builder = FieldOfTanks(RNG(0), field)
		builder.generate()
		builder.map_key(floor=MockFloor())
		builder.map_key(wall=MockWall())
		builder.make_grid()
		self.assertEqual(field.tostring(lambda c: c.sprite.sprite), unittest.dedent("""\
		.............
		.####..##....
		.####.####...
		.####.####...
		.####..##....
		.............
		....#.####...
		.#..#.####...
		...#..####...
		.####.####...
		.............
		.............
		.............
		"""))
