from clckwrkbdgr import unittest
import textwrap
from clckwrkbdgr.math import Point, Size, Matrix, Rect
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr import pcg
from .. import builders
from .. import items, appliances
from ..mock import *

def make_builder(rng, grid_or_size):
	builder = MockBuilder(rng, grid_or_size)
	builder.map_key(**({
		'exit':lambda: 'exit',
		}))
	builder.map_key(
			monster = lambda pos,*data: ('monster',) + data + (pos,),
			item = lambda *data: ('item',) + data,
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
	def should_generate_amount_by_free_cells(self):
		builder = make_builder(RNG(0), (10, 10))
		builder.generate()
		gen_amount = builder.amount_by_free_cells(4)
		self.assertEqual(gen_amount(), 14)
		self.assertEqual(gen_amount(), 14)
	def should_generate_amount_by_fixed_range(self):
		builder = make_builder(RNG(0), (10, 10))
		builder.generate()
		gen_amount = builder.amount_fixed(4)
		self.assertEqual(gen_amount(), 4)
		self.assertEqual(gen_amount(), 4)
		gen_amount = builder.amount_fixed((4, 10))
		self.assertEqual(gen_amount(), 5)
		self.assertEqual(gen_amount(), 5)
		gen_amount = builder.amount_fixed(4, 10)
		self.assertEqual(gen_amount(), 7)
		self.assertEqual(gen_amount(), 8)

class TestDistribution(unittest.TestCase):
	def should_distribute_entities_in_uniform_manner(self):
		rng = RNG(0)
		builder = UniformSquatters(rng, Size(20, 20))
		builder.generate()
		_monsters = list(builder.make_actors())
		_items = list(builder.make_items())

		self.maxDiff = None
		self.assertEqual(sorted(_monsters), sorted([
			('slime', Point(7, 5)),
			('plant',  Point(16, 3)),
			('rodent', Point(12, 15)),
			('slime',  Point(16, 9)),
			('rodent', Point(12, 4)),
			]))
		self.assertEqual(sorted(_items), sorted([
			items.ItemAtPos(Point(6, 8), ('healing potion',)),
			]))
	def should_distribute_entities_by_weights(self):
		rng = RNG(0)
		builder = WeightedSquatters(rng, Size(20, 20))
		builder.generate()
		_monsters = list(builder.make_actors())
		_items = list(builder.make_items())

		self.maxDiff = None
		self.assertEqual(sorted(_monsters), sorted([
			('slime', Point(7, 5)),
			('slime',  Point(16, 3)),
			('rodent', Point(12, 15)),
			('rodent',  Point(16, 9)),
			('rodent', Point(12, 4)),
			]))
		self.assertEqual(sorted(_items), sorted([
			items.ItemAtPos(Point(6, 8), ('healing potion',)),
			]))

class TestBuilder(unittest.TestCase):
	def should_generate_dungeon(self):
		rng = RNG(0)
		builder = make_builder(rng, Size(20, 20))
		builder.generate()
		self.maxDiff = None
		_appliances = sorted(builder.make_appliances())
		self.assertEqual(_appliances, sorted([
			appliances.ObjectAtPos(Point(2, 10), 'start'),
			appliances.ObjectAtPos(Point(9, 12), 'exit'),
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
			items.ItemAtPos(Point(7, 16), ('item', 'mcguffin')),
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
