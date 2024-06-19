from __future__ import division
from .math import Point

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
		return seq[self.range(len(seq))]

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
