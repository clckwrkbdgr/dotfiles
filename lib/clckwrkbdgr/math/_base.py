from __future__ import absolute_import
import itertools
import operator
import math
from collections import namedtuple
from functools import total_ordering
import vintage

@total_ordering
class Vector(object):
	""" Represents N-dim vector.
	Supported operations:
	- iteration over items;
	- serialization (pickle, jsonpickle);
	- accessing items: vector[i];
	- math operations: <=>, +, -, * (scalar), / (scalar), // (scalar).
	"""
	def __new__(cls, *args): # pragma: no cover FIXME to prevent issues with deserializing from old namedtuple format.
		instance = super(Vector, cls).__new__(cls)
		instance.__init__(*args)
		return instance
	def __init__(self, *values):
		""" Creates vector from values, iterables or Vector:
		Vector(0, 1, 2, ...)
		Vector([0, 1, 2, ...])
		Vector(Vector(0, 1, 2, ...))
		"""
		if len(values) == 1:
			if isinstance(values[0], Vector):
				values = values[0].values
			else:
				values = values[0]
		self.values = list(values)
	def __str__(self): # pragma: no cover
		return str(self.values)
	def __repr__(self): # pragma: no cover
		return str(type(self)) + str(self)
	def __hash__(self):
		return hash(tuple(self.values))
	def __iter__(self):
		return iter(self.values)
	def __getitem__(self, attr):
		return self.values[attr]
	def __getstate__(self):
		return self.values
	def __setstate__(self, state):
		self.values = state
	def __eq__(self, other):
		return other is not None and self.values == Vector(other).values
	def __ne__(self, other):
		return not (self == other)
	def __lt__(self, other):
		return other is not None and self.values < Vector(other).values
	def __abs__(self):
		return type(self)(list(map(abs, self.values)))
	def __add__(self, other):
		return type(self)(list(map(operator.add, self.values, Vector(other).values)))
	def __sub__(self, other):
		return type(self)(list(map(operator.sub, self.values, Vector(other).values)))
	def __mul__(self, other):
		return type(self)(list(_ * other for _ in self.values))
	def __floordiv__(self, other):
		return type(self)(list(_ // other for _ in self.values))
	def __truediv__(self, other): # pragma: no cover -- py3 only
		return type(self)(list(_ / other for _ in self.values))
	def __div__(self, other): # pragma: no cover -- py2 only
		return type(self)(list(_ / other for _ in self.values))

class Point(Vector): # pragma: no cover
	""" Convenience type definition for 2D vector
	with access to first two elements under aliases .x and .y
	"""
	def __setstate__(self, state):
		if isinstance(state, dict):
			self.values = [state['x'], state['y']]
		else:
			super(Point, self).__setstate__(state)
	@property
	def x(self): return self.values[0]
	@x.setter
	def x(self, value): self.values[0] = value
	@property
	def y(self): return self.values[1]
	@y.setter
	def y(self, value): self.values[1] = value
	def neighbours(self):
		""" Returns all neighbours including the copy of original point:
		All points in 3x3 square around the original one.
		"""
		for x in [-1, 0, 1]:
			for y in [-1, 0, 1]:
				yield Point(self.x + x, self.y + y)

def distance(point_a, point_b):
	""" Amount of cells between two points. """
	return max(abs(point_a.x - point_b.x), abs(point_a.y - point_b.y))

class Direction:
	""" Direction on a rectangular grid.
	"""
	NONE = Point(0,  0)
	LEFT = Point(-1,  0)
	DOWN = Point( 0, +1)
	UP = Point( 0, -1)
	RIGHT = Point(+1,  0)
	UP_LEFT = Point(-1, -1)
	UP_RIGHT = Point(+1, -1)
	DOWN_LEFT = Point(-1, +1)
	DOWN_RIGHT = Point(+1, +1)

	@classmethod
	def from_points(cls, start, target):
		""" Returns vector from start to target as a Direction value. """
		shift = target - start
		shift = Point(
				shift.x // abs(shift.x) if shift.x else 0,
				shift.y // abs(shift.y) if shift.y else 0,
				)
		return shift

class Size(Vector): # pragma: no cover
	""" Convenience type definition for 2D vector
	with access to first two elements under aliases .with and .height
	"""
	def __setstate__(self, state):
		if isinstance(state, dict):
			self.values = [state['x'], state['y']]
		else:
			super(Size, self).__setstate__(state)
	@property
	def width(self): return self.values[0]
	@width.setter
	def width(self, value): self.values[0] = value
	@property
	def height(self): return self.values[1]
	@height.setter
	def height(self, value): self.values[1] = value
	@property
	def x(self): return self.width
	@property
	def y(self): return self.height
	def iter_points(self):
		""" Iterates over all available positions withing rect of this size.
		See Matrix.keys().
		"""
		return iter(Point(x, y) for y, x in itertools.product(range(self.height), range(self.width)))

class Rect(object):
	""" Represents rectangle. """
	def __init__(self, topleft, size):
		""" Creates rectangle from topleft (Point or tuple of 2 elements)
		and size (Size or tuple of 2 elements).
		"""
		self._topleft = Point(topleft)
		self._size = Size(size)
	def __str__(self): # pragma: no cover
		return str((self._topleft, self._size))
	def __repr__(self): # pragma: no cover
		return str(type(self)) + str(self)
	def __hash__(self):
		return hash( (self.topleft, self.size) )
	def __setstate__(self, data): # pragma: no cover
		self._topleft = data['topleft']
		self._size = data['size']
	def __getstate__(self): # pragma: no cover
		return {'topleft':self._topleft, 'size':self._size}
	def __eq__(self, other):
		return other is not None and self._topleft == other._topleft and self._size == other._size
	@property
	def width(self): return self._size.width
	@property
	def height(self): return self._size.height
	@property
	def size(self): return self._size
	@property
	def top(self): return self._topleft.y
	@property
	def left(self): return self._topleft.x
	@property
	def bottom(self): return self._topleft.y + self._size.height - 1
	@property
	def right(self): return self._topleft.x + self._size.width - 1
	@property
	def topleft(self): return Point(self.left, self.top)
	@property
	def bottomright(self): return Point(self.right, self.bottom)
	def contains(self, pos, with_border=False):
		pos = Point(pos)
		if with_border:
			return self.left <= pos.x <= self.right and self.top <= pos.y <= self.bottom
		return self.left < pos.x < self.right and self.top < pos.y < self.bottom

@vintage.deprecated('Moved to clckwrkbdgr.math.grid.Matrix')
def Matrix(*args, **kwargs): # pragma: no cover
	from . import grid
	return grid.Matrix(*args, **kwargs)

@vintage.deprecated('Moved to clckwrkbdgr.math.grid.HexGrid')
def HexGrid(*args, **kwargs): # pragma: no cover
	from . import grid
	return grid.HexGrid(*args, **kwargs)

@vintage.deprecated('Moved to clckwrkbdgr.math.grid.get_neighbours()')
def get_neighbours(*args, **kwargs): # pragma: no cover
	from . import grid
	return grid.get_neighbours(*args, **kwargs)

def sign(value):
	""" Returns -1 for negative values, +1 for positive values and 0 for zero.
	Type of resulting value depends on type of argument.
	"""
	return value and type(value)(math.copysign(1, value))
