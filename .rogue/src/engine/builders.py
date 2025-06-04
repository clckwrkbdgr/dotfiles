import copy
from clckwrkbdgr.math import Matrix
from clckwrkbdgr import pcg

class Builder(object): # pragma: no cover -- TODO
	""" Basic generator for maps with content.
	Subclasses should generate content (maps, objects)
	using key names, which should be mapped using map_key()
	and will be used later to produce (bake) actual map.
	"""
	def __init__(self, rng, grid):
		""" Creates builder over existing grid.
		It will be used to fill in make_grid().
		"""
		self.rng = rng
		self.size = grid.size
		self.dest_grid = grid
		self.mapping = {}
	def map_key(self, **mapping):
		""" Maps keys to objects. Objects will be pasted
		via copy.deepcopy() upon making actual map.
		"""
		self.mapping.update(mapping)

	def generate(self):
		""" Main method. Calls all overloaded methods to generate
		abstract content. Use make_*() to compile actual content.
		"""
		grid = Matrix(self.size, None)
		self.fill_grid(grid)
		self.grid = grid
	def make_grid(self):
		""" Compiles generated abstract map and returns result grid.
		If grid was passed to the builder's init, it will be re-used.
		"""
		if self.grid:
			for pos in self.grid:
				mapped_object = self.mapping[self.grid.cell(pos)]
				self.dest_grid.set_cell(pos, copy.deepcopy(mapped_object))
			self.grid = None
		return self.dest_grid

	def point(self):
		""" Generates random point on map. """
		return pcg.point(self.rng, self.size)

	def fill_grid(self, grid):
		""" Should populate grid (terrain). """
		raise NotImplementedError()
