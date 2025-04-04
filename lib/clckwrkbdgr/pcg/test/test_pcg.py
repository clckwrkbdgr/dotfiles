from clckwrkbdgr import unittest
from .. import _base as pcg

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

class TestPrimitives(unittest.TestCase):
	def should_select_random_item_based_on_weights(self):
		rng = pcg.RNG(12345)
		self.assertEqual(pcg.weighted_choices(rng,
			[(1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'), (5, 'e')], amount=10),
						 ['d', 'c', 'e', 'b', 'd', 'd', 'd', 'c', 'c', 'c'],
						 )
