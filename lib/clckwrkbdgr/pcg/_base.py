from __future__ import division
import random
try:
	random.choices
except AttributeError: # pragma: no cover -- py3.5
	random.choices = lambda *args, **kwargs: random_choices(random, *args, **kwargs)

def random_choices(rng, population, weights, k=1):
	""" Re-implementation of random.choices for backward compatibility purposes.
	"""
	n = len(population)
	cumulative_weights = []
	it = iter(weights)
	cumulative_weights.append(next(it))
	for value in it: # py2 itertools has no accumulate()
		cumulative_weights.append(cumulative_weights[-1] + value)
	assert len(cumulative_weights) == n
	total = cumulative_weights[-1] + 0.0   # convert to float
	import itertools, bisect
	return [population[bisect.bisect(cumulative_weights, rng.random() * total, 0, n - 1)]
			for i in itertools.repeat(None, k)]

class RNG:
	""" Linear Conguential Generator.
	Parameters from glibc.
	"""
	mult_a = 1103515245
	inc_c = 12345
	mod_m = 2**31
	def __init__(self, seed=None):
		""" If seed is omitted, current timestamp is used as seed.

		Raw current value is available through `.value`.
		Original seed is available as `.seed`.
		"""
		if seed is None: # pragma: no cover
			import time
			seed = int(time.time())
		self.seed = seed
		self.value = seed
	def random(self): return self.get()
	def get(self):
		""" Returns value [0; 1) """
		self.value = (self.mult_a * self.value + self.inc_c) % self.mod_m
		return self.value / self.mod_m
	def range(self, min_value, max_value=None):
		""" Random int number in range [a; b) or [0; a). """
		if max_value is None:
			min_value, max_value = 0, min_value
		return int(self.get() * (max_value - min_value)) + min_value
	def choice(self, seq):
		""" Evenly distributed choice. """
		return seq[self.range(len(seq))]
	def choices(self, population, weights, k=1):
		""" Weighted choice from population,
		based on corresponding list of weights.
		"""
		return random_choices(self, population, weights, k=k)

def weighted_choices(rng, weights_and_items, amount=1):
	""" Makes random weighted choice based on list of tuples: (<weight>, <item>), ...
	Returns list of items.
	"""
	args = zip(*(map(reversed, weights_and_items)))
	return rng.choices(*args, k=amount)
