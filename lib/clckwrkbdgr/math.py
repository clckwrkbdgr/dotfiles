import itertools
import copy
import operator
from collections import namedtuple
from functools import total_ordering

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
		""" Creates vector from values:
		Vector(0, 1, 2, ...)
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
	def __iter__(self):
		return iter(self.values)
	def __getitem__(self, attr):
		return self.values[attr]
	def __getstate__(self):
		return self.values
	def __setstate__(self, state):
		self.values = state
	def __eq__(self, other):
		return self.values == Vector(other).values
	def __lt__(self, other):
		return self.values < Vector(other).values
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
	@property
	def x(self): return self.values[0]
	@x.setter
	def x(self, value): self.values[0] = value
	@property
	def y(self): return self.values[1]
	@y.setter
	def y(self, value): self.values[1] = value

class Size(Vector): # pragma: no cover
	""" Convenience type definition for 2D vector
	with access to first two elements under aliases .with and .height
	"""
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

class Matrix(object):
	""" Represents 2D matrix.
	"""
	def __init__(self, dims, default=None):
		""" Creates Matrix with specified dimensions (iterable len=2) and fills with specified default value:
		Matrix( (3, 3), default='.')
		Matrix( Size(3, 3), default='.')
		"""
		if isinstance(dims, Matrix):
			other = dims
			self.dims = copy.copy(other.dims)
			self.data = copy.copy(other.data)
			return
		self.resize(dims, default=default)
	def resize(self, dims, default=None):
		""" Resizes matrix to a new size.
		NOTE: Clears map and fills with new default values.
		"""
		width, height = dims
		assert isinstance(width, int)
		assert isinstance(height, int)
		assert width > 0
		assert height > 0
		self.dims = Size(width, height)
		# TODO maybe clearing is not the best idea, maybe I should keep old values wherever is possible.
		self.data = [copy.deepcopy(default) for _ in range(width * height)]
	def size(self):
		""" Returns iterable of size (two-component). """
		return self.dims
	def width(self):
		return self.dims.width
	def height(self):
		return self.dims.height
	def valid(self, pos):
		""" Returns True if pos is within Matrix boundaries. """
		pos = Point(pos)
		return 0 <= pos.x < self.dims.width and 0 <= pos.y < self.dims.height
	def cell(self, pos):
		""" Returns value of specified cell.
		Raises KeyError is position is invalid.
		"""
		pos = Point(pos)
		if not self.valid(pos):
			raise KeyError('Invalid cell position: {0}'.format(pos))
		return self.data[pos.x + pos.y * self.dims.width]
	def set_cell(self, pos, value):
		""" Sets value of specified cell.
		Raises KeyError is position is invalid.
		"""
		pos = Point(pos)
		if not self.valid(pos):
			raise KeyError('Invalid cell position: {0}'.format(pos))
		self.data[pos.x + pos.y * self.dims.width] = value
	def __iter__(self):
		""" Iterates over all available positions. """
		return iter(map(Point, itertools.product(range(self.dims.width), range(self.dims.height))))
