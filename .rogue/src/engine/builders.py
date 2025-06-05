import copy
from collections import defaultdict
from clckwrkbdgr.math import Matrix
from clckwrkbdgr import pcg

class Builder(object): # pragma: no cover -- TODO
	""" Basic generator for maps with content.
	Subclasses should generate content (maps, objects)
	using key names, which should be mapped using map_key()
	or via Mapping inner class
	and will be used later to produce (bake) actual map.
	"""
	class Mapping(object):
		""" Default way to define mapping on global level.
		Each Builder instance will also have additional mapping via map_key(),
		which takes priority over class mapping.
		Class variables and their values will be treated as keys/objects.
		Class (or static) methods can be used as callable mappings.
		"""
		pass

	def __init__(self, rng, grid):
		""" Creates builder over existing grid.
		It will be used to fill in make_grid().
		"""
		self.rng = rng
		self.size = grid.size
		self.dest_grid = grid
		self.mapping = {}
	def _get_mapping(self, key):
		result = self.mapping.get(key)
		if result:
			return result
		return getattr(self.Mapping, key)
	def map_key(self, **mapping):
		""" Maps keys to objects/types/callables.
		See make_*() for details on how each layer works with mapped objects.

		"""
		self.mapping.update(mapping)

	# Generation sequence.

	def generate(self):
		""" Main method. Calls all overloaded methods to generate
		abstract content. Use make_*() to compile actual content.
		"""
		grid = Matrix(self.size, None)
		self.fill_grid(grid)
		self.actors = defaultdict(list)
		for actor_data in self.generate_actors(grid):
			pos, actor_data = actor_data[0], actor_data[1:]
			self.actors[pos].append(actor_data)
		self.grid = grid
	def make_grid(self):
		""" Compiles generated abstract map and returns result grid.
		If grid was passed to the builder's init, it will be re-used.
		Mapped objects will be pasted via copy.deepcopy().
		"""
		if self.grid:
			for pos in self.grid:
				mapped_object = self._get_mapping(self.grid.cell(pos))
				self.dest_grid.set_cell(pos, copy.deepcopy(mapped_object))
			self.grid = None
		return self.dest_grid
	def make_actors(self):
		""" Iterates over actor data and yields ready actor objects
		according to mapping.
		If mapped object as a type, its init should accept position
		as the first argument, and the rest of the data goes as the
		remaining arguments.
		If mapped object is a callable, it should accept full list
		of arguments (pos,)+actor_data and return fully constructed object.
		Otherwise it is considered a proper object and will be copied
		via copy.deepcopy()
		"""
		for pos, actors in self.actors.items():
			for actor_data in actors:
				key, actor_data = actor_data[0], actor_data[1:]
				mapped_object = self._get_mapping(key)
				if callable(mapped_object):
					yield mapped_object(pos, *actor_data)
				else:
					yield copy.deepcopy(mapped_object)

	# PCG routines and controls.

	def has_actor(self, pos):
		""" Returns True if position is already occupied by some actor.
		"""
		return pos in self.actors
	def point(self):
		""" Generates random point on map. """
		return pcg.point(self.rng, self.size)

	# Customization.

	def fill_grid(self, grid):
		""" Should populate grid (terrain). """
		raise NotImplementedError()
	def generate_actors(self, grid):
		""" Should yield actors data as tuples: (pos, key, <custom data...>)
		"""
		yield
