from ._base import Point, Size
import copy
import itertools
import vintage

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

class EndlessMatrix(object):
	""" Sort of a "window" over an endless map.
	The global map is divided into blocks of the same size, at every moment only 9 of them are accessible:
	the central one (which holds current position of interest) and 3x3 belt of surrounding maps.
	After position of interest is moved, method recalibrate(new_pos) should be called
	to recalculate available blocks.
	"""
	def __init__(self, block_size, builder, default_value=None):
		""" Create 3x3 blocks of given size and fill them using builder callable (accepts a Matrix object).
		Default filling value can be supplied. It will also be used for recalibration.
		At the start, anchor pos is considered to be at (0, 0) of the central block.
		"""
		self.builder = builder
		self.block_size = Size(block_size)
		self.shift = Point(0, 0) - self.block_size
		self.blocks = Matrix((3, 3))
		self.default_value = default_value
		for row in range(self.blocks.height):
			for col in range(self.blocks.width):
				self.blocks.set_cell((col, row), Matrix(self.block_size, self.default_value))
				self.builder(self.blocks.cell((col, row)))
	def __getstate__(self): # pragma: no cover
		return {
				'block_size' : self.block_size,
				'shift' : self.shift,
				'blocks' : self.blocks,
				'default_value' : self.default_value,
				}
	def __setstate__(self, state): # pragma: no cover
		self.__dict__.update(state)
	def __eq__(self, other):
		return type(other) is type(self) \
				and self.block_size == other.block_size \
				and self.shift == other.shift \
				and self.blocks == other.blocks
	def valid(self, pos):
		""" Returns True if global position is contained within any of the available 3x3 blocks. """
		relative_pos = Point(pos) - self.shift
		block_pos = Point(relative_pos.x // self.block_size.width, relative_pos.y // self.block_size.height)
		if not self.blocks.valid(block_pos):
			return False
		block = self.blocks.cell(block_pos)
		block_rel_pos = Point(relative_pos.x % self.block_size.width, relative_pos.y % self.block_size.height)
		return block.valid(block_rel_pos)
	def cell(self, pos):
		""" Returns cell at the global position, if valid.
		Otherwise returns None.
		"""
		relative_pos = Point(pos) - self.shift
		block_pos = Point(relative_pos.x // self.block_size.width, relative_pos.y // self.block_size.height)
		if not self.blocks.valid(block_pos):
			return None
		block = self.blocks.cell(block_pos)
		block_rel_pos = Point(relative_pos.x % self.block_size.width, relative_pos.y % self.block_size.height)
		return block.cell(block_rel_pos)
	def recalibrate(self, anchor_pos):
		""" Recalculates and shifts block configuration so the central one
		will always contain anchor pos.
		Rebuilds blocks with builder callable.
		"""
		relative_pos = Point(anchor_pos) - self.shift
		block_pos = Point(relative_pos.x // self.block_size.width, relative_pos.y // self.block_size.height)
		if block_pos == Point(1, 1):
			return
		block_shift = block_pos - Point(1, 1)
		new_blocks = Matrix((3, 3))
		for row in range(new_blocks.height):
			for col in range(new_blocks.width):
				pos = Point(col, row)
				old_pos = pos + block_shift
				if self.blocks.valid(old_pos):
					new_blocks.set_cell(pos, self.blocks.cell(old_pos))
				else:
					new_blocks.set_cell(pos, Matrix(self.block_size, self.default_value))
					self.builder(new_blocks.cell(pos))
		self.blocks = new_blocks
		self.shift += Point(
				block_shift.x * self.block_size.width,
				block_shift.y * self.block_size.height,
				)

class NestedGrid: # pragma: no cover -- TODO
	""" A grid, divided into sub-grids recursively.
	I.e. a cell of top-level grid is a NestedGrid itself, and so on.
	At the bottom level, each cell is of actual cell type.
	All subgrids on each level are of the same size.
	Cells can be adressed both via global positions
	or via Coord object (nested set of coordinates). Number of coord elements
	should correspond to the depth of the NestedGrid.
	"""

	class Coord:
		""" A way to address cells on NestedGrids. """
		def __init__(self, *coords):
			""" Creates coord object from given sequence of Points. """
			self.values = list(map(Point, coords))
		def save(self, stream):
			""" Saves object to a stream. """
			for value in self.values:
				stream.write(value.x)
				stream.write(value.y)
		def load(self, stream):
			""" Loads object from a stream. """
			for value in self.values:
				value.x = stream.read(int)
				value.y = stream.read(int)
		def get_global(self, nested_grid):
			""" Compresses into global position on the specified NestedGrid.
			"""
			size = Size(1, 1)
			result = self.values[-1]
			for index, value in enumerate(reversed(self.values[:-1])):
				size.width *= nested_grid.sizes[-1-index].width
				size.height *= nested_grid.sizes[-1-index].height
				result += Point(value.x * size.width, value.y * size.height)
			return result
		def __eq__(self, other):
			if not isinstance(other, NestedGrid.Coord):
				raise TypeError("Cannot compare NestedGrid.Coord with {0}".format(type(other)))
			return self.values == other.values
		def __ne__(self, other):
			return not (self == other)
		def __repr__(self):
			return 'x'.join(map(str, self.values))
		def __str__(self):
			return ';'.join((
					''.join('{0:02X}'.format(value.x) for value in self.values),
					''.join('{0:02X}'.format(value.y) for value in self.values),
					))
		@classmethod
		def from_global(cls, pos, nested_grid):
			""" Splits global pos on the specified NestedGrid into a Coord object.
			"""
			sizes = [Size(1, 1)]
			for index in range(len(nested_grid.sizes) - 1):
				sizes.append(Size(
					sizes[-1].width * nested_grid.sizes[-1-index].width,
					sizes[-1].height * nested_grid.sizes[-1-index].height,
					))
			values = []
			for size in reversed(sizes):
				values.append(Point(pos.x // size.width, pos.y // size.width))
				pos = Point(pos.x % size.width, pos.y % size.height)
			return cls(*values)

	def __init__(self, sizes, data_classes, cell_type):
		""" Creates grid of given sizes and and with specified
		cell_type as a basic element.
		Depth is calculated from the number of given sizes.
		Each level of subgrid (including the top one) can contain additional
		.data field for subgrid-wide data (e.g. placed objects, map properties,
		etc). If data_class on some level is None, data object for that level
		is not created (always None) and resulting grid also becomes sparse
		(i.e. some subgrid cells on that level are allowed to be None.
		This can be used on topmost levels to keep only needed subgrids, thus
		preventing unnecessary memory overload.
		Number of sizes and data classes should match.

		E.g.: ((256, 256), (32, 32), (16, 16)), (None, RegionData, LocalData), Cell
		Creates global sparse map of 256x256 regions, each region has .data=RegionData() and is 32x32 local maps, each map has .data=LocalData() and is 16x16 grid of Cell objects. Total of 131072x131072 cells.
		"""
		assert len(sizes) == len(data_classes), (sizes, data_classes)
		self.cells = Matrix(sizes[0], None)
		self.nested_sizes = tuple(map(Size, sizes[1:]))
		self.data_class = data_classes[0]
		self.data = self.data_class() if self.data_class else None
		self.nested_data = data_classes[1:]
		self.cell_type = cell_type
		self._valid_cell = None
	def save(self, stream):
		""" Save full grid to the stream.
		Automatically handles sparse grids.
		"""
		stream.write(self.cells.width)
		stream.write(self.cells.height)
		for tile_index in self.cells:
			tile = self.cells.cell(tile_index)
			if self.data_class:
				tile.save(stream)
			else:
				if tile:
					stream.write('.')
					tile.save(stream)
				else:
					stream.write('')
		if self.data_class:
			stream.write(self.data)
	def load(self, stream):
		""" Loads full grid from the stream.
		Grid object should be created beforehand with correct sizes, data classes and cell type.
		Automatically handles sparse grids.
		"""
		size = Size(stream.read(int), stream.read(int))
		self.cells = Matrix(size, None)
		for tile_index in self.cells:
			if not self.data_class:
				tile = stream.read()
				if not tile:
					continue
			if self.nested_sizes:
				tile = NestedGrid((Size(1, 1),) + self.nested_sizes[1:], self.nested_data, self.cell_type)
				tile.load(stream)
			else:
				tile = self.cell_type.load(stream)
			self.cells.set_cell(tile_index, tile)
			self._valid_cell = tile_index
		if self.data_class:
			self.data = stream.read(type(self.data))
	def make_subgrid(self, pos):
		""" Initializes subgrid at specified position.
		Required for each cell in non-sparse grids.
		"""
		value = NestedGrid(self.nested_sizes, self.nested_data, self.cell_type)
		self.cells.set_cell(pos, value)
		self._valid_cell = pos
		return value
	def valid(self, coord):
		""" Returns True is Coord points to a valid nested chain of grids and a cell.
		"""
		subgrid = self
		for pos in coord.values:
			if subgrid is None:
				return False
			if not subgrid.cells.valid(pos):
				return False
			subgrid = subgrid.cells.cell(pos)
		return True
	def cell(self, coord):
		""" Returns actual cell at specified Coord.
		"""
		cell = self
		for pos in coord.values:
			cell = cell.cells.cell(pos)
		return cell
	def get_data(self, coord):
		""" Returns list of data object for every affected level at specified Coord.
		I.e. global grid data, data for subgrid which contains coord and so on.
		"""
		result = [self.data]
		subgrid = self
		for pos in coord.values[:-1]:
			subgrid = subgrid.cells.cell(pos)
			result.append(subgrid.data)
		return result
	@property
	def sizes(self):
		""" List of nested sizes (see c-tor). """
		return (self.cells.size,) + self.nested_sizes
	@property
	def full_size(self):
		""" Full size in cells of the current grid. """
		result = self.cells.size
		for size in self.nested_sizes:
			result = Size(
					result.width * size.width,
					result.height * size.height,
					)
		return result
