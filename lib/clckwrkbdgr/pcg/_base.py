from __future__ import division
import random
try:
	random.choices
except AttributeError: # pragma: no cover -- py3.5
	random.choices = lambda *args, **kwargs: random_choices(random, *args, **kwargs)
from clckwrkbdgr.math import Point, Size

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
	def randrange(self, min_value, max_value=None): return self.range(min_value, max_value)
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

class TryCheck:
	""" Generates value using generator and supplied args.
	Checks every generated value using checker callable,
	returns value only if checker returns True.
	If all tryouts have failed, returns last generated value.

	Example:
	TryCheck(random.randrange).check(lambda x: x % 2 == 0).tryouts(1000)(0, 100)
	"""
	def __init__(self, generator):
		""" Default checker allows everything.
		Default tryouts is 1000.
		"""
		self.generator = generator
		self.checker = lambda _:True
		self.counter = 1000
	def check(self, checker):
		self.checker = checker
		return self
	def tryouts(self, amount):
		self.counter = amount
		return self
	def __call__(self, *args, **kwargs):
		""" Generate value until checker returns True.
		"""
		result = None
		while self.counter > 0:
			result = self.generator(*args, **kwargs)
			if self.checker(result):
				break
			self.counter -= 1
		return result

def weighted_choices(rng, weights_and_items, amount=1):
	""" Makes random weighted choice based on list of tuples: (<weight>, <item>), ...
	Returns list of items.
	"""
	args = zip(*(map(reversed, weights_and_items)))
	return rng.choices(*args, k=amount)

def point(rng, size):
	""" Boundaries are NOT included. """
	return Point(rng.randrange(size.width or 1), rng.range(size.height or 1))

def point_in_rect(rng, rect, with_boundaries=False):
	shrink = 0 if with_boundaries else 1
	return Point(
			rng.randrange(rect.left + shrink, rect.right + 1 - shrink),
			rng.randrange(rect.top + shrink, rect.bottom + 1 - shrink),
			)

def size(rng, min_size, max_size):
	""" Boundaries are included. """
	return Size(
			rng.randrange(min_size.width, max_size.width + 1),
			rng.randrange(min_size.height, max_size.height + 1),
			)
