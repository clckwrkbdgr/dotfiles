import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from .. import _base as pcg
from ...math import Point, Size

class TestRNG(unittest.TestCase):
	def should_select_random_item_based_on_weights(self):
		rng = pcg.RNG(12345)
		self.assertEqual(rng.choices('abcde', [1,2,3,4,5]), ['d'])
		rng = pcg.RNG(12345)
		self.assertEqual(rng.choices('abcde', [1,2,3,4,5], k=10), ['d', 'c', 'e', 'b', 'd', 'd', 'd', 'c', 'c', 'c'])

class MockRNG(pcg.RNG):
	def __init__(self, mock_sequence):
		self.sequence = mock_sequence
	def get(self):
		value = self.sequence.pop(0)
		assert value is not None and 0 <= value < 1
		return value

class TestPrimitives(unittest.TestCase):
	def should_generate_raw_pos(self):
		rng = MockRNG([0.5, 0.6, 0.7, 0.8])
		self.assertEqual(pcg.pos(rng, Size(80, 25)), Point(40, 15))
		self.assertEqual(pcg.pos(rng, Size(20, 20)), Point(14, 16))
	def should_generate_pos_with_check(self):
		rng = MockRNG([0.5, 0.6, 0.7, 0.8])
		self.assertEqual(pcg.pos(rng, Size(80, 25), check=lambda p: p!=Point(40, 15)), Point(56, 20))
	def should_run_out_of_valid_points(self):
		rng = MockRNG([0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.1, 0.2])
		self.assertEqual(pcg.pos(rng, Size(80, 25), check=lambda p: p.x < 10, counter=5), Point(8, 5))
		rng = MockRNG([0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.1, 0.2])
		self.assertEqual(pcg.pos(rng, Size(80, 25), check=lambda p: p.x < 10, counter=2), Point(72, 23))
	def should_select_random_item_based_on_weights(self):
		rng = pcg.RNG(12345)
		self.assertEqual(pcg.weighted_choices(rng,
			[(1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'), (5, 'e')], amount=10),
						 ['d', 'c', 'e', 'b', 'd', 'd', 'd', 'c', 'c', 'c'],
						 )
