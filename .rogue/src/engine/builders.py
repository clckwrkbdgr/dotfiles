import copy
from collections import defaultdict
from clckwrkbdgr.math import Matrix, Size
from clckwrkbdgr import pcg
from clckwrkbdgr import utils

class EntityDistribution(object):
	""" Basic distribution of entities from the list. """
	def __init__(self, rng, entities):
		self.rng = rng
		self.entities = list(entities)
	def __call__(self): # pragma: no cover
		""" Should return single entity from the list. """
		raise NotImplementedError()

class UniformDistribution(EntityDistribution):
	""" All entities have the same probability weight. """
	def __call__(self):
		return self.rng.choice(self.entities) if len(self.entities) != 1 else self.entities[0]

class WeightedDistribution(EntityDistribution):
	""" Weighted choice from a weighted entity list.
	Each item should be a tuple of (weight, <data>).
	Returns data without weight.
	Weight is a number - the greater the number, the more probable the choice.
	"""
	def __call__(self):
		return pcg.weighted_choices(self.rng, self.entities)[0]

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

		self.grid = grid
		self.appliances = defaultdict(list)
		self.actors = defaultdict(list)
		self.items = defaultdict(list)

		for appliance_data in self.generate_appliances():
			if appliance_data is None: # pragma: no cover -- Empty generator.
				continue
			pos, appliance_data = appliance_data[0], appliance_data[1:]
			self.appliances[pos].append(appliance_data)

		for actor_data in self.generate_actors():
			if actor_data is None: # pragma: no cover -- Empty generator.
				continue
			pos, actor_data = actor_data[0], actor_data[1:]
			self.actors[pos].append(actor_data)

		for item_data in self.generate_items():
			if item_data is None: # pragma: no cover -- Empty generator.
				continue
			pos, item_data = item_data[0], item_data[1:]
			self.items[pos].append(item_data)
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

	# Generation controls and checks.
	# All of these are available only after call to fill_grid()

	def has_actor(self, pos):
		""" Returns True if position is already occupied by some actor.
		"""
		return pos in self.actors
	def has_appliance(self, pos):
		""" Returns True if position is already occupied by some appliance.
		"""
		return pos in self.appliances
	def is_open(self, pos): # pragma: no cover
		""" Should return True is given grid cell is considered "open",
		i.e. passable.
		By default all cells are open.
		"""
		return True
	def is_accessible(self, pos):
		""" Should return True is given grid cell is considered "accessible",
		i.e. open and available to place appliances or drop any items there.
		By default all open cells are accessible except ones
		already occupied by appliances.
		"""
		return self.is_open(pos) and not self.has_appliance(pos)
	def is_free(self, pos):
		""" Should return True is given pos is considered "vacant",
		i.e. accessible and/or available to putting appliances/actors/items.
		By default all open cells are free except ones occupied by appliances
		and/or other actors.
		"""
		return self.is_accessible(pos) and not self.has_actor(pos)

	# PCG routines.

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
	def amount_by_free_cells(self, cell_per_entity, is_free=None):
		""" Returns callback:
		Returns number of entities that could be distributen over free cells
		with specified cell_per_entity ratio.
		Default is_free check corresponds to is_free method,
		i.e. passable and not occupied by any appliance or actor.
		"""
		is_free = is_free or self.is_free
		def _actual():
			total_free_cells = sum(1 for pos in self.grid.size.iter_points() if is_free(pos))
			return int(total_free_cells / float(cell_per_entity))
		return _actual
	def amount_fixed(self, min_amount, max_amount=None):
		""" Returns callback:
		Returns random number of entities in specified range.
		If only one argument is given and it's a tuple, it is considered a tuple
		of (min_amount, max_amount).
		If only argument is given and it's a number, it is returned as fixed
		value.
		"""
		if max_amount is None and utils.is_collection(min_amount):
			min_amount, max_amount = min_amount
		def _actual():
			if max_amount is not None:
				return self.rng.randrange(min_amount, max_amount)
			return min_amount
		return _actual
	def distribute(self, distribution, entities, generate_amount, is_free=None):
		""" Yields entities (pos+data) randomly distributed
		using given EntityDistribution class for amount generated by generate_amount (see various self.amount_*)
		Entity list format should correspond to the one that is accepted by
		given distribution.
		Default is_free check corresponds to is_free method,
		i.e. passable and not occupied by any appliance or actor.
		"""
		distribution = distribution(self.rng, entities)
		is_free = is_free or self.is_free
		for _ in range(generate_amount()):
			yield (self.point(is_free),) + distribution()

	# Customization.

	def fill_grid(self, grid): # pragma: no cover
		""" Should populate grid (terrain).

		Terrain cells cannot be moved or removed.
		Destructible terrain should be implemented as switching cell content/type.
		"""
		raise NotImplementedError()
	def generate_appliances(self): # pragma: no cover
		""" Should yield appliance data as tuples: (pos, key, <custom data...>)

		Appliance is an object that is considered a part of surroundings,
		can be interacted with, can be removed (destructed),
		potentially can be moved,
		but cannot move on its own, act on its own and cannot be picked up.
		"""
		yield
	def generate_actors(self): # pragma: no cover
		""" Should yield actors data as tuples: (pos, key, <custom data...>)

		Actors are movable objects that can interact with surroundings.
		"""
		yield
	def generate_items(self): # pragma: no cover
		""" Should yield item data as tuples: (pos, key, <custom data...>)

		Items are objects that cannot interact or move,
		only picked up/dropped down.
		"""
		yield
