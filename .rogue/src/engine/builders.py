import copy
from clckwrkbdgr.math import Matrix
from clckwrkbdgr import pcg

class Builder(object): # pragma: no cover -- TODO
	def __init__(self, rng, grid):
		self.rng = rng
		self.size = grid.size
		self.dest_grid = grid
		self.mapping = {}
	def map_key(self, **mapping):
		self.mapping.update(mapping)

	def generate(self):
		grid = Matrix(self.size, None)
		self.fill_grid(grid)
		self.grid = grid
	def get_grid(self):
		if self.grid:
			for pos in self.grid:
				mapped_object = self.mapping[self.grid.cell(pos)]
				self.dest_grid.set_cell(pos, copy.deepcopy(mapped_object))
			self.grid = None
		return self.dest_grid

	def point(self):
		return pcg.point(self.rng, self.size)

	def fill_grid(self, grid):
		raise NotImplementedError()
