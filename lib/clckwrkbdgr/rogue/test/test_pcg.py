from clckwrkbdgr import unittest
from .. import pcg

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
