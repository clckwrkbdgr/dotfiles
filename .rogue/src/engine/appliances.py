from clckwrkbdgr.utils import classfield
import six
import inspect

class Appliance(object):
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown object')
	def __str__(self):
		return self.name
	def __repr__(self):
		return '{0}({1})'.format(type(self).__name__, self.name)

	@classmethod
	def load(cls, reader):
		""" Loads info about Appliance object (class name), constructs actual instance
		and optionally loads subclass-specific data.
		Classes are serialized as their class names, so reader metainfo with key 'Appliances'
		should be a dict-like object which stores all required classes under their class names.
		Subclasses should have default c-tor.
		Subclasses should override this method as non-classmethod (regular instance method)
		which loads subclass-specific data only.
		"""
		type_name = reader.read()
		registry = reader.get_meta_info('Appliances')
		obj_type = registry[type_name]
		assert obj_type is cls or issubclass(obj_type, cls)
		obj = obj_type()
		if six.PY2: # pragma: no cover -- TODO
			is_overridden_as_instance_method = obj_type.load.__self__ is not None
		else: # pragma: no cover -- TODO
			is_overridden_as_instance_method = inspect.ismethod(obj_type.load)
		if not is_overridden_as_instance_method:
			obj.load(reader)
		return obj
	def save(self, writer):
		""" Default implementation writes only class name.
		Override to write additional subclass-specific properties.
		Don't forget to call super().save()!
		"""
		writer.write(type(self).__name__)

class ObjectAtPos(object): # pragma: no cover -- TODO
	def __init__(self, pos, obj):
		self.pos = pos
		self.obj = obj
	def __repr__(self):
		return '{0} @{1}'.format(repr(self.obj), repr(self.pos))
	def __str__(self):
		return '{0} @{1}'.format(self.obj, self.pos)
	def __lt__(self, other):
		return (self.pos, self.obj) < (other.pos, other.obj)
	def __eq__(self, other):
		if isinstance(other, type(self)):
			return (self.pos, self.obj) == (other.pos, other.obj)
		return self.obj == other
	def __iter__(self):
		return iter((self.pos, self.obj))
	@classmethod
	def load(cls, reader):
		obj = reader.read(Appliance)
		pos = reader.read_point()
		return cls(pos, obj)
	def save(self, writer):
		writer.write(self.obj)
		writer.write(self.pos)
