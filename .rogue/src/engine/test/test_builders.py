from clckwrkbdgr import unittest
import textwrap
from clckwrkbdgr.math import Point, Size, Matrix, Rect
from clckwrkbdgr.pcg import RNG
from clckwrkbdgr import pcg
from .. import builders
from .. import items, appliances
from ..mock import *

def make_builder(rng, grid_or_size):
	builder = DungeonFloor(rng, grid_or_size)
	builder.map_key(**({
		'exit':lambda: 'exit',
		}))
	builder.map_key(
			butterfly = lambda pos, color: Butterfly(pos, color=color),
			note = lambda text: ScribbledNote(text),
			)
	return builder

class TestUtilities(unittest.TestCase):
	def should_detect_placed_actors(self):
		rng = RNG(0)
		grid = Matrix((10, 5), 'X')
		builder = make_builder(rng, grid)
		builder.generate()

		self.assertTrue(builder.has_actor(Point(6, 3)))
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
		self.assertEqual(gen_amount(), 7)
		self.assertEqual(gen_amount(), 8)
		gen_amount = builder.amount_fixed(4, 10)
		self.assertEqual(gen_amount(), 9)
		self.assertEqual(gen_amount(), 8)

class TestDistribution(unittest.TestCase):
	def should_distribute_entities_in_uniform_manner(self):
		rng = RNG(0)
		builder = UniformSquat(rng, Size(20, 20))
		builder.generate()
		_monsters = list(builder.make_actors())
		_items = list(builder.make_items())

		self.maxDiff = None
		self.assertEqual(sorted(map(lambda c:(c.name, c.pos), _monsters)), sorted([
			('goblin', Point(9, 10)),
			('dragonfly',  Point(7, 16)),
			('rat', Point(4, 14)),
			('rat', Point(5, 12)),
			('rat',  Point(8, 14)),
			]))
		self.assertEqual(sorted(map(lambda c:(c.pos, c.item.name), _items)), sorted([
			(Point(11, 4), 'potion'),
			]))
	def should_distribute_entities_by_weights(self):
		rng = RNG(0)
		builder = WeightedSquat(rng, Size(20, 20))
		builder.generate()
		_monsters = list(builder.make_actors())
		_items = list(builder.make_items())

		self.maxDiff = None
		self.assertEqual(sorted(map(lambda c:(c.name, c.pos), _monsters)), sorted([
			('goblin', Point(7, 16)),
			('rat',  Point(4, 14)),
			('rat', Point(5, 12)),
			('rat',  Point(8, 14)),
			('rat', Point(9, 10)),
			]))
		self.assertEqual(sorted(map(lambda c:(c.pos, c.item.name), _items)), sorted([
			(Point(11, 4), 'potion'),
			]))

class TestBuilder(unittest.TestCase):
	def should_generate_dungeon(self):
		rng = RNG(0)
		builder = make_builder(rng, Size(20, 20))
		builder.generate()
		self.maxDiff = None
		_appliances = sorted(map(repr, builder.make_appliances()))
		self.assertEqual(_appliances, sorted(map(repr, [
			appliances.ObjectAtPos(Point(2, 10), 'start'),
			appliances.ObjectAtPos(Point(7, 5), Statue('goddess')),
			appliances.ObjectAtPos(Point(9, 12), 'exit'),
			])))
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
		self.assertEqual(grid.tostring(lambda c:c.sprite.sprite), expected)

		_monsters = list(builder.make_actors())
		self.assertEqual(sorted(map(lambda c:(c.name, c.pos, c.color), _monsters)), sorted([
			('butterfly', Point(7, 16), 'red'),
			]))

		_items = list(builder.make_items())
		self.assertEqual(sorted(map(lambda c:(c.pos, c.item.name, c.item.text), _items)), sorted([
			(Point(3, 5), 'note', 'welcome'),
			]))
	def should_generate_dungeon_on_existing_grid(self):
		rng = RNG(0)
		grid = Matrix((10, 5), None)
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
		self.assertEqual(grid.tostring(lambda c:c.sprite.sprite), expected)
