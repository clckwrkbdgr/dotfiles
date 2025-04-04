from __future__ import division
from ..math import Point
from clckwrkbdgr import pcg as _pcg
from clckwrkbdgr.pcg import weighted_choices

class RNG(_pcg.RNG):
	pass

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
