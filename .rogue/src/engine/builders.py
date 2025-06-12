import copy
from collections import defaultdict
from clckwrkbdgr.math import Matrix, Size
from clckwrkbdgr import pcg

class Builder(object):
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

		Order of generation:
		- fill_grid
		- generate_appliances (only grid is available)
		- generate_actors (available: grid, appliances)
		- generate_items (available: grid, appliances, actors)
		"""
		grid = Matrix(self.size, None)
		self.fill_grid(grid)
		assert not hasattr(self, 'exit_pos')
		assert not hasattr(self, 'start_pos')

		self.appliances = defaultdict(list)
		for appliance_data in self.generate_appliances(grid):
			if appliance_data is None: # pragma: no cover -- Empty generator.
				continue
			pos, appliance_data = appliance_data[0], appliance_data[1:]
			self.appliances[pos].append(appliance_data)

		self.actors = defaultdict(list)
		for actor_data in self.generate_actors(grid):
			if actor_data is None: # pragma: no cover -- Empty generator.
				continue
			pos, actor_data = actor_data[0], actor_data[1:]
			self.actors[pos].append(actor_data)

		self.items = defaultdict(list)
		for item_data in self.generate_items(grid):
			if item_data is None: # pragma: no cover -- Empty generator.
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
		"""
		for pos, entities in position_map.items():
			for entity_data in entities:
				key, entity_data = entity_data[0], entity_data[1:]
				mapped_object = self._get_mapping(key)
				yield mapped_object(pos, *entity_data)
	def make_appliances(self):
		""" Yields ready appliance objects according to mapping.
		See make_entities() for details.
		"""
		for _ in self.make_entities(self.appliances):
			yield _
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
	def has_appliance(self, pos):
		""" Returns True if position is already occupied by some appliance.
		"""
		return pos in self.appliances
	def point(self, check=None):
		""" Generates random point on map.
		If check is supplied, it should be a callable(Point)
		and should return True if given position is free.
		"""
		if check:
			return pcg.TryCheck(pcg.point).check(check)(self.rng, self.size)
		return pcg.point(self.rng, self.size)
	def point_in_rect(self, rect, with_boundaries=False):
		""" Generates random point within rect area. """
		return pcg.point_in_rect(self.rng, rect, with_boundaries=with_boundaries)

	# Customization.

	def fill_grid(self, grid): # pragma: no cover
		""" Should populate grid (terrain).

		Terrain cells cannot be moved or removed.
		Destructible terrain should be implemented as switching cell content/type.
		"""
		raise NotImplementedError()
	def generate_appliances(self, grid): # pragma: no cover
		""" Should yield appliance data as tuples: (pos, key, <custom data...>)

		Appliance is an object that is considered a part of surroundings,
		can be interacted with, can be removed (destructed),
		potentially can be moved,
		but cannot move on its own, act on its own and cannot be picked up.
		"""
		yield
	def generate_actors(self, grid): # pragma: no cover
		""" Should yield actors data as tuples: (pos, key, <custom data...>)

		Actors are movable objects that can interact with surroundings.
		"""
		yield
	def generate_items(self, grid): # pragma: no cover
		""" Should yield item data as tuples: (pos, key, <custom data...>)

		Items are objects that cannot interact or move,
		only picked up/dropped down.
		"""
		yield
