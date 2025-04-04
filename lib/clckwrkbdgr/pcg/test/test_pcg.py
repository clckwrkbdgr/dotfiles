from clckwrkbdgr import unittest
from .. import _base as pcg
from clckwrkbdgr.math import Point, Size, Rect

class TestRNG(unittest.TestCase):
	def should_generate_random_numbers(self):
		rng = pcg.RNG(0)
		self.assertAlmostEqual(rng.get(), 0.0000057)
		self.assertEqual(rng.value, 12345)
		self.assertAlmostEqual(rng.get(), 0.655154)
		self.assertEqual(rng.value, 1406932606)
	def should_reproduce_sequences_by_seed(self):
		rng = pcg.RNG(12345)
		self.assertAlmostEqual(rng.get(), 0.655154)
		self.assertEqual(rng.value, 1406932606)
		self.assertAlmostEqual(rng.get(), 0.3048143)
		self.assertEqual(rng.value, 654583775)
	def should_get_numbers_within_range(self):
		rng = pcg.RNG(12345)
		self.assertEqual(rng.range(100), 65)
		rng = pcg.RNG(12345)
		self.assertEqual(rng.range(0, 100), 65)
		rng = pcg.RNG(12345)
		self.assertEqual(rng.range(20, 100), 72)
	def should_select_random_item_from_sequence(self):
		rng = pcg.RNG(12345)
		self.assertEqual(rng.choice('abcde'), 'd')
		rng = pcg.RNG(12345)
		self.assertEqual(rng.choice([6,5,4,3,2]), 3)
	def should_select_random_item_based_on_weights(self):
		rng = pcg.RNG(12345)
		self.assertEqual(rng.choices('abcde', [1,2,3,4,5]), ['d'])
		rng = pcg.RNG(12345)
		self.assertEqual(rng.choices('abcde', [1,2,3,4,5], k=10), ['d', 'c', 'e', 'b', 'd', 'd', 'd', 'c', 'c', 'c'])

class TestUtils(unittest.TestCase):
	def should_generate_value_with_check(self):
		rng = pcg.RNG(0)
		self.assertEqual(pcg.TryCheck(pcg.point).check(lambda p: p!=Point(0, 16))(rng, Size(80, 25)), Point(24, 16))
	def should_run_out_of_valid_points(self):
		rng = pcg.RNG(0)
		self.assertEqual(pcg.TryCheck(pcg.point).check(lambda p: p.y > 50).tryouts(5)(rng, Size(80, 25)), Point(29, 6))
		rng = pcg.RNG(0)
		self.assertEqual(pcg.TryCheck(pcg.point).check(lambda p: p.y > 50).tryouts(2)(rng, Size(80, 25)), Point(24, 16))

class TestPrimitives(unittest.TestCase):
	def should_select_random_item_based_on_weights(self):
		rng = pcg.RNG(12345)
		self.assertEqual(pcg.weighted_choices(rng,
			[(1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'), (5, 'e')], amount=10),
						 ['d', 'c', 'e', 'b', 'd', 'd', 'd', 'c', 'c', 'c'],
						 )
	def should_generate_raw_pos(self):
		rng = pcg.RNG(0)
		self.assertEqual(pcg.point(rng, Size(80, 25)), Point(0, 16))
		self.assertEqual(pcg.point(rng, Size(20, 20)), Point(6, 13))
	def should_generate_raw_size(self):
		rng = pcg.RNG(0)
		self.assertEqual(pcg.size(rng, Size(3, 3), Size(80, 25)), Point(3, 18))
		self.assertEqual(pcg.size(rng, Size(0, 0), Size(20, 20)), Point(6, 14))
	def should_generate_point_in_rect(self):
		rng = pcg.RNG(0)
		self.assertEqual(pcg.point_in_rect(rng, Rect((0, 0), Size(80, 25))), Point(1, 16))
		self.assertEqual(pcg.point_in_rect(rng, Rect((10, 10), Size(20, 20))), Point(16, 23))
