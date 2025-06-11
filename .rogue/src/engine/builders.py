import copy
from collections import defaultdict
from clckwrkbdgr.math import Matrix, Size
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
		Non-keyword mapping names can be defined via dict field Mapping._
		"""
		_ = None
		pass

	def __init__(self, rng, grid_or_size):
		""" Creates builder over grid.
		Accepts either existing grid (which will be used to fill in make_grid()),
		or a size (in this case new grid will be created and returned in make_grid()).
		"""
		self.rng = rng
		if isinstance(grid_or_size, Matrix):
			self.size = grid_or_size.size
		else:
			self.size = Size(grid_or_size)
		if isinstance(grid_or_size, Matrix):
			self.dest_grid = grid_or_size
		else:
			self.dest_grid = None
		self.mapping = {}
	def _get_mapping(self, key):
		result = self.mapping.get(key)
		if result:
			return result
		if hasattr(self.Mapping, '_') and self.Mapping._:
			result = self.Mapping._.get(key)
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
			if actor_data is None: # Empty generator.
				continue
			pos, actor_data = actor_data[0], actor_data[1:]
			self.actors[pos].append(actor_data)

		self.items = defaultdict(list)
		for item_data in self.generate_items(grid):
			if item_data is None: # Empty generator.
				continue
			pos, item_data = item_data[0], item_data[1:]
			self.items[pos].append(item_data)

		self.grid = grid
	def make_grid(self):
		""" Compiles generated abstract map and returns result grid.
		If existing grid was passed to the builder's init, it will be re-used.
		Mapped objects will be pasted via copy.deepcopy().
		"""
		if self.grid:
			if self.dest_grid is None:
				self.dest_grid = self.grid
			for pos in self.grid:
				mapped_object = self._get_mapping(self.grid.cell(pos))
				self.dest_grid.set_cell(pos, copy.deepcopy(mapped_object))
			self.grid = None
		return self.dest_grid
	def make_entities(self, position_map):
		""" Iterates over entities data and yields ready entities
		according to mapping.
		Position map is a dict {pos:[list of entities tied to that pos]}
		If mapped object as a type, its init should accept position
		as the first argument, and the rest of the data goes as the
		remaining arguments.
		If mapped object is a callable, it should accept full list
		of arguments (pos,)+entity_data and return fully constructed object.
		Otherwise it is considered a proper object and will be copied
		via copy.deepcopy()
		"""
		for pos, entities in position_map.items():
			for entity_data in entities:
				key, entity_data = entity_data[0], entity_data[1:]
				mapped_object = self._get_mapping(key)
				if callable(mapped_object):
					yield mapped_object(pos, *entity_data)
				else:
					yield copy.deepcopy(mapped_object)
	def make_actors(self):
		""" Yields actor objects according to mapping.
		See make_entities() for details.
		"""
		for _ in self.make_entities(self.actors):
			yield _
	def make_items(self):
		""" Yields ready item objects according to mapping.
		See make_entities() for details.
		"""
		for _ in self.make_entities(self.items):
			yield _

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
	def generate_items(self, grid):
		""" Should yield item data as tuples: (pos, key, <custom data...>)
		"""
		yield
