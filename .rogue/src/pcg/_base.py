from __future__ import division
from ..math import Point
from clckwrkbdgr import pcg as _pcg

class RNG(_pcg.RNG):
	def choices(self, population, weights, k=1):
		""" Weighted choice from population,
		based on corresponding list of weights.
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
		return [population[bisect.bisect(cumulative_weights, self.get() * total, 0, n - 1)]
				for i in itertools.repeat(None, k)]

def pos(rng, size, check=None, counter=1000):
	""" Generates random Point withing given Size.
	If check function is supplied, only the first matching value is returned.
	If no matching values are generated and counter is out, returns last non-matching value.
	"""
	result = Point(rng.range(size.width), rng.range(size.height))
	if check:
		while counter > 0:
			result = Point(rng.range(size.width), rng.range(size.height))
			if check(result):
				break
			counter -= 1
	return result

def weighted_choices(rng, weights_and_items, amount=1):
	""" Makes random weighted choice based on list of tuples: (<weight>, <item>), ...
	Returns list of items.
	"""
	args = zip(*(map(reversed, weights_and_items)))
	return rng.choices(*args, k=amount)
