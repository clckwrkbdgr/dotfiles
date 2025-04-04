from __future__ import division
from ..math import Point
from clckwrkbdgr import pcg as _pcg

def pos(rng, size, check=None, counter=1000):
	""" Generates random Point withing given Size.
	If check function is supplied, only the first matching value is returned.
	If no matching values are generated and counter is out, returns last non-matching value.
	"""
	_pcg.point(rng, size) # FIXME work around legacy bug which scrapped the first result
	return _pcg.TryCheck(_pcg.point).check(check).tryouts(counter)(rng, size)
