import inspect
import six
from clckwrkbdgr.utils import classfield
import clckwrkbdgr.utils

class Entity(object):
	""" The base for any entity in the game: actor, terrain, item etc.
	"""
	_metainfo_key = None
	sprite = classfield('_sprite', None)
	name = classfield('_name', 'unknown')
	def __str__(self):
		return self.name
	def __repr__(self):
		return '{0}({1})'.format(type(self).__name__, self.name)

	def save(self, writer):
		""" Default implementation writes only class name.
		Override to write additional subclass-specific properties.
		Don't forget to call super().save()!
		"""
		writer.write(type(self).__name__)

	@classmethod
	def load(cls, reader, _additional_init=None):
		""" Loads info about object (class name), constructs actual instance
		and optionally loads subclass-specific data.
		Classes are serialized as their class names, so reader has to have metainfo with key (_metainfo_key)
		should be a dict-like object which stores all required classes under their class names.
		Subclasses should have default c-tor.
		Subclasses should override this method as non-classmethod (regular instance method)
		which loads subclass-specific data only.
		"""
		type_name = reader.read()
		registry = reader.get_meta_info(cls._metainfo_key)
		obj_type = registry[type_name]
		assert obj_type is cls or issubclass(obj_type, cls)
		if _additional_init:
			obj = obj_type(_additional_init(reader))
		else:
			obj = obj_type()
		if six.PY2: # pragma: no cover -- TODO
			is_overridden_as_instance_method = obj_type.load.__self__ is not None
		else: # pragma: no cover -- TODO
			is_overridden_as_instance_method = inspect.ismethod(obj_type.load)
		if not is_overridden_as_instance_method:
			obj.load(reader)
		return obj

class EntityAtPos(object):
	_entity_type = None
	def __init__(self, pos, entity):
		self.pos = pos
		self.entity = entity
	def __repr__(self):
		return '{0} @{1}'.format(repr(self.entity), repr(self.pos))
	def __str__(self):
		return '{0} @{1}'.format(self.entity, self.pos)
	def __lt__(self, other):
		return (self.pos, self.entity) < (other.pos, other.entity)
	def __eq__(self, other):
		if isinstance(other, type(self)):
			return (self.pos, self.entity) == (other.pos, other.entity)
		return self.entity == other
	def __iter__(self):
		return iter((self.pos, self.entity))
	@classmethod
	def load(cls, reader):
		entity = reader.read(cls._entity_type)
		pos = reader.read_point()
		return cls(pos, entity)
	def save(self, writer):
		writer.write(self.entity)
		writer.write(self.pos)

class MakeEntity(object):
	""" Creates builders for bare-properties-based classes to create subclass in one line.
	>>> make_weapon = MakeEntity(Item, '_sprite _name _attack')
	>>> make_weapon('Dagger', Sprite('(', None), 'dagger', 1)
	"""
	def __init__(self, base_classes, *properties):
		""" Properties are either list of strings, or a single strings with space-separated identifiers. """
		self.base_classes = base_classes if clckwrkbdgr.utils.is_collection(base_classes) else (base_classes,)
		self.properties = properties
		if len(self.properties) == 1 and ' ' in self.properties[0]:
			self.properties = self.properties[0].split()
	def __call__(self, class_name, *values):
		""" Creates class object and puts it into global namespace.
		Values should match properties given at init.
		"""
		assert len(self.properties) == len(values), len(values)
		entity_class = type(class_name, self.base_classes, dict(zip(self.properties, values)))
		caller_globals = inspect.currentframe().f_back.f_globals
		caller_globals[class_name] = entity_class
		return entity_class

class EntityClassDistribution(object):
	""" Distributes entities based on probability.

	>>> norm_monsters = EntityClassDistribution(lambda depth: max(0, (depth-2)))
	>>> norm_monsters << Ant
	>>> norm_monsters.get_distribution(depth)
	"""
	def __init__(self, prob):
		self.prob = prob
		self.classes = []
	def __lshift__(self, entity_class):
		self.classes.append(entity_class)
	def __iter__(self):
		return iter(self.classes)
	def get_distribution(self, param):
		if callable(self.prob):
			value = self.prob(param)
		else:
			value = self.prob
		return [(value, entity_class) for entity_class in self.classes]
