from clckwrkbdgr.math import Point
from clckwrkbdgr.utils import classfield
import inspect
import six

class Actor(object):
	""" Basic actor.
	Has no properties except for sprite/name/position.
	"""
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown creature')

	def __init__(self, pos):
		self.pos = Point(pos) if pos else None
	def __str__(self):
		return self.name
	def __repr__(self):
		return '{0}({1} @{2})'.format(type(self).__name__, self.name, self.pos)

	@classmethod
	def load(cls, reader):
		""" Loads basic info about Actor object (class name and pos),
		constructs actual instance and optionally loads subclass-specific data.
		Classes are serialized as their class names, so reader metainfo with key 'Actors'
		should be a dict-like object which stores all required classes under their class names.
		Subclasses should have default c-tor.
		Subclasses should override this method as non-classmethod (regular instance method)
		which loads subclass-specific data only.
		"""
		type_name = reader.read()
		registry = reader.get_meta_info('Actors')
		obj_type = registry[type_name]
		assert obj_type is cls or issubclass(obj_type, cls)
		pos = reader.read_point()
		obj = obj_type(pos)
		if six.PY2: # pragma: no cover -- TODO
			is_overridden_as_instance_method = obj_type.load.__self__ is not None
		else: # pragma: no cover -- TODO
			is_overridden_as_instance_method = inspect.ismethod(obj_type.load)
		if not is_overridden_as_instance_method:
			obj.load(reader)
		return obj
	def save(self, writer):
		""" Default implementation writes only class name and position.
		Override to write additional subclass-specific properties.
		Don't forget to call super().save()!
		"""
		writer.write(type(self).__name__)
		writer.write(self.pos)

class Monster(Actor):
	pass
