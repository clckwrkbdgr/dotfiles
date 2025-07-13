from clckwrkbdgr.utils import classfield
import six
import inspect

class Item(object):
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown item')
	def __str__(self):
		return self.name
	def __repr__(self):
		return '{0}({1})'.format(type(self).__name__, self.name)

	@classmethod
	def load(cls, reader):
		""" Loads info about Item object (class name), constructs actual instance
		and optionally loads subclass-specific data.
		Classes are serialized as their class names, so reader metainfo with key 'Items'
		should be a dict-like object which stores all required classes under their class names.
		Subclasses should have default c-tor.
		Subclasses should override this method as non-classmethod (regular instance method)
		which loads subclass-specific data only.
		"""
		type_name = reader.read()
		registry = reader.get_meta_info('Items')
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

class Wearable(object):
	""" Trait for items that can be worn as outfit.
	"""
	pass

class ItemAtPos(object): # pragma: no cover -- TODO
	def __init__(self, pos, item):
		self.pos = pos
		self.item = item
	def __repr__(self):
		return '{0} @{1}'.format(repr(self.item), repr(self.pos))
	def __str__(self):
		return '{0} @{1}'.format(self.item, self.pos)
	def __lt__(self, other):
		return (self.pos, self.item) < (other.pos, other.item)
	def __eq__(self, other):
		if isinstance(other, type(self)):
			return (self.pos, self.item) == (other.pos, other.item)
		return self.item == other
	def __iter__(self):
		return iter((self.pos, self.item))
	@classmethod
	def load(cls, reader):
		item = reader.read(Item)
		pos = reader.read_point()
		return cls(pos, item)
	def save(self, writer):
		writer.write(self.item)
		writer.write(self.pos)
