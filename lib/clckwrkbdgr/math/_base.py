from __future__ import absolute_import
import itertools
import copy
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

class CallableIntProperty(int): # pragma: no cover
	@vintage.deprecated('Calling property as method is deprecated.')
	def __call__(self): return self

class CallableSizeProperty(Size): # pragma: no cover
	@vintage.deprecated('Calling property as method is deprecated.')
	def __call__(self): return self

class Matrix(object):
	""" Represents 2D matrix.
	"""
	def __init__(self, dims, default=None):
		""" Creates Matrix with specified dimensions (iterable len=2) and fills with specified default value:
		a = Matrix( (3, 3), default='.')
		b = Matrix( Size(3, 3), default='.')
		c = Matrix(b) # Creates deepcopy of another matrix.
		"""
		if isinstance(dims, Matrix):
			other = dims
			self.dims = copy.copy(other.dims)
			self.data = copy.deepcopy(other.data)
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
	def fill(self, topleft, downright, value):
		""" Fills rectangle (including borders) with specified value. """
		topleft = Point(topleft)
		downright = Point(downright)
		for x in range(topleft.x, downright.x + 1):
			for y in range(topleft.y, downright.y + 1):
				self.set_cell(Point(x, y), value)
	def clear(self, value): # pragma: no cover
		""" Fills the whole map with specified value. """
		return self.fill(Point(0, 0), Point(self.width - 1, self.height - 1), value)
	@property
	def size(self):
		""" Returns iterable of size (two-component). """
		return CallableSizeProperty(self.dims)
	@property
	def width(self):
		return CallableIntProperty(self.dims.width)
	@property
	def height(self):
		return CallableIntProperty(self.dims.height)
	def __repr__(self): # pragma: no cover
		return 'Matrix(({0}, {1}))'.format(*self.dims)
	def __eq__(self, other):
		if not isinstance(other, Matrix):
			raise TypeError("Cannot compare matrix with {0}".format(type(other)))
		if self.dims != other.dims:
			return False
		return self.data == other.data
	def __ne__(self, other):
		return not (self == other)
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
	def keys(self):
		""" Iterates over all available positions. """
		return self.dims.iter_points()
	def values(self):
		""" Iterates over all available values. """
		return iter(self.data)
	def __iter__(self):
		""" Iterates over all available positions, see keys(). """
		return self.keys()
	def find(self, value):
		""" Yields positions where value is found. """
		for pos in self.keys():
			if self.cell(pos) == value:
				yield pos
	def find_if(self, condition):
		""" Yields positions where values match given condition. """
		for pos in self.keys():
			if condition(self.cell(pos)):
				yield pos
	def transform(self, transformer):
		""" Returns new instance of matrix with same dimensions
		and transformer(c) applied for each cell.
		"""
		new_matrix = Matrix(self.dims)
		new_matrix.data = [transformer(copy.deepcopy(c)) for c in self.data]
		return new_matrix
	@classmethod
	def from_iterable(cls, iterable):
		""" Creates matrix from iterable of iterables (set of rows).
		All rows should be of equal width, otherwise ValueError is raised.
		"""
		data = []
		width, height = None, 0
		for row in iterable:
			row = list(row)
			if width is None:
				width = len(row)
			elif len(row) != width:
				raise ValueError('Not all lines are of equal width ({0})'.format(width))
			data.extend(row)
			height += 1
		m = cls(Size(width, height))
		m.data = data
		return m
	@classmethod
	def fromstring(cls, multiline_string, transformer=None):
		""" Creates matrix from multiline string.
		All lines should be of equal width, otherwise ValueError is raised.
		If transformer is specified, it should be callable that takes single argument (single string char) and transforms into matrix element. By default stored as string chars.
		"""
		lines = multiline_string.splitlines()
		width, height = max(map(len, lines)), len(lines)
		if any(len(line) != width for line in lines):
			raise ValueError('Not all lines are of equal width ({0})'.format(width))
		m = cls(Size(width, height))
		if not transformer:
			transformer = lambda c: c
		m.data = list(transformer(c) for c in itertools.chain.from_iterable(lines))
		return m
	def tostring(self, transformer=None):
		""" Returns multiline string representation of matrix.
		Each line represents single row.
		If transformer is specified, it should be callable that takes matrix element and converts to string representation. By default usual str() is used.
		"""
		result = ''
		if not transformer:
			transformer = str
		for start in range(0, len(self.data), self.dims[0]):
			for c in self.data[start:start+self.dims[0]]:
				result += transformer(c)
			result += '\n'
		return result

class HexGrid(object):
	r""" Represents grid of hexagonal cells.
	 __    __    __
	/  \__/  \__/  \
	\__/  \__/  \__/
	/  \__/  \__/  \
	\__/  \__/  \__/
	/  \__/  \__/  \
	\__/  \__/  \__/
	   \__/  \__/   
	"""
	def __init__(self, rows, columns, default=None):
		self.data = Matrix((columns, rows), default=default)
	@property
	def rows(self):
		return self.data.height
	@property
	def columns(self):
		return self.data.width
	def get_cell(self, point):
		return self.data.cell(point)
	def set_cell(self, point, value):
		return self.data.set_cell(point, value)
	def get_neighbours(self, point):
		shifts = [Point(0, -1),
			Point(-1, 0), Point(1, 0),
			Point(-1, 1), Point(1, 1),
				Point(0, 1),
				]
		point = Point(point)
		for shift in shifts:
			neigh = point + shift
			if self.data.valid(neigh):
				yield neigh
	def to_string(self):
		result = ''
		for column in range(self.columns):
			if column % 2 == 0:
				result += ' __'
			else:
				result += '   '
		result += ' \n'
		for row in range(self.rows):
			for column in range(self.columns):
				if column % 2 == 0:
					content = str(self.data.cell((column, row)) or '')
					content = (content + '  ')[:2]
					result += '/' + content + '\\'
				else:
					result += '__'
			result += '\n'
			for column in range(self.columns):
				if column % 2 == 0:
					result += '\\__/'
				else:
					content = str(self.data.cell((column, row)) or '')
					content = (content + '  ')[:2]
					result += content
			result += '\n'
		for column in range(self.columns):
			if column == 0:
				result += '   '
			elif column % 2 == 0:
				result += '/  '
			else:
				result += '\\__'
		result += ' \n'
		return result

def get_neighbours(matrix, pos, check=None, with_diagonal=False):
	""" Yields points adjacent to given pos (valid points only).
	By default checks only orthogonal cells.
	If with_diagonal is True, checks also diagonal adjacent cells.
	If check is not none, it is applied to value at each pos
	and yields only if callable returns True.
	"""
	pos = Point(pos)
	neighbours = [
			pos + Point(1, 0),
			pos + Point(0, 1),
			pos - Point(1, 0),
			pos - Point(0, 1),
			]
	if with_diagonal:
		neighbours += [
				pos + Point( 1,  1),
				pos + Point(-1,  1),
				pos + Point( 1, -1),
				pos + Point(-1, -1),
				]
	for p in neighbours:
		if not matrix.valid(p):
			continue
		if check and not check(matrix.cell(p)):
			continue
		yield p

def sign(value):
	""" Returns -1 for negative values, +1 for positive values and 0 for zero.
	Type of resulting value depends on type of argument.
	"""
	return value and type(value)(math.copysign(1, value))
