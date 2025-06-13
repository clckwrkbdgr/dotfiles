from clckwrkbdgr import unittest
import textwrap
from clckwrkbdgr.math import Point, Size, Matrix, Rect
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr import pcg
from .. import builders

class MockBuilder(builders.Builder):
	class Mapping:
		wall = '#'
		_ = {
			'floor': '.',
			'water': '~',
			}
		@staticmethod
		def start(pos): return (pos, 'start')
	def is_open(self, pos):
		return self.grid.cell(pos) == 'floor'

	def fill_grid(self, grid):
		for x in range(self.size.width):
			grid.set_cell((x, 0), 'wall')
			grid.set_cell((x, self.size.height - 1), 'wall')
		for y in range(self.size.height):
			grid.set_cell((0, y), 'wall')
			grid.set_cell((self.size.width - 1, y), 'wall')
		for x in range(1, self.size.width - 1):
			for y in range(1, self.size.height - 1):
				grid.set_cell((x, y), 'floor')
		obstacle_pos = self.point_in_rect(Rect((0, 0), self.size))
		grid.set_cell(obstacle_pos, 'wall')
		obstacle_pos = self.point()
		grid.set_cell(obstacle_pos, 'water')
	def generate_appliances(self):
		yield self.point(self.is_accessible), 'start'
		yield self.point(self.is_accessible), 'exit'
	def generate_actors(self):
		yield self.point(self.is_free), 'monster', 'angry'
	def generate_items(self):
		yield self.point(self.is_accessible), 'item', 'mcguffin'

def make_builder(rng, grid_or_size):
	builder = MockBuilder(rng, grid_or_size)
	builder.map_key(**({
		'exit':lambda pos: (pos, 'exit'),
		}))
	builder.map_key(
			monster = lambda pos,*data: ('monster',) + data + (pos,),
			item = lambda pos,*data: ('item',) + data + (pos,),
			)
	return builder

class TestUtilities(unittest.TestCase):
	def should_detect_placed_actors(self):
		rng = RNG(0)
		grid = Matrix((10, 5), 'X')
		builder = make_builder(rng, grid)
		builder.generate()
		self.assertTrue(builder.has_actor(Point(1, 1)))
		self.assertFalse(builder.has_actor(Point(1, 2)))

class TestBuilder(unittest.TestCase):
	def should_generate_dungeon(self):
		rng = RNG(0)
		builder = make_builder(rng, Size(20, 20))
		builder.generate()
		self.maxDiff = None
		appliances = sorted(builder.make_appliances())
		self.assertEqual(appliances, sorted([
			(Point(2, 10), 'start'),
			(Point(9, 12), 'exit'),
			]))
		grid = builder.make_grid()
		expected = textwrap.dedent("""\
				####################
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				##.................#
				#.....~............#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				####################
				""")
		self.assertEqual(grid.tostring(), expected)

		_monsters = list(builder.make_actors())
		self.assertEqual(_monsters, [
			('monster', 'angry', Point(7, 5)),
			])

		_items = list(builder.make_items())
		self.assertEqual(_items, [
			('item', 'mcguffin', Point(7, 16)),
			])
	def should_generate_dungeon_on_existing_grid(self):
		rng = RNG(0)
		grid = Matrix((10, 5), 'X')
		builder = make_builder(rng, grid)
		builder.generate()
		builder.make_grid()
		expected = textwrap.dedent("""\
				##########
				#........#
				##.......#
				#..~.....#
				##########
				""")
		self.assertEqual(grid.tostring(), expected)
