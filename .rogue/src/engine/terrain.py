from clckwrkbdgr.utils import classfield
import six
import inspect

class Terrain(object):
	sprite = classfield('_sprite', None)
	name = classfield('_name', 'void')
	passable = classfield('_passable', True) # allow free movement.
	remembered = classfield('_remembered', None) # sprite for "remembered" state, where it is not seen directly, but was visited before.
	allow_diagonal = classfield('_allow_diagonal', True) # allows diagonal movement to and from this cell. Otherwise only orthogonal movement is allowed.
	dark = classfield('_dark', False) # if True, no light is present and it is not considered transparent if further than 1 cell from the center.

	@classmethod
	def load(cls, reader):
		""" Loads info about Terrain object (class name), constructs actual instance
		and optionally loads subclass-specific data.
		Classes are serialized as their class names, so reader metainfo with key 'Terrain'
		should be a dict-like object which stores all required classes under their class names.
		Subclasses should have default c-tor.
		Subclasses should override this method as non-classmethod (regular instance method)
		which loads subclass-specific data only.
		"""
		terrain_type_name = reader.read()
		registry = reader.get_meta_info('Terrain')
		terrain_type = registry[terrain_type_name]
		assert terrain_type is cls or issubclass(terrain_type, cls)
		obj = terrain_type()
		if six.PY2: # pragma: no cover -- TODO
			is_overridden_as_instance_method = terrain_type.load.__self__ is not None
		else: # pragma: no cover -- TODO
			is_overridden_as_instance_method = inspect.ismethod(terrain_type.load)
		if not is_overridden_as_instance_method:
			obj.load(reader)
		return obj
	def save(self, writer):
		""" Default implementation writes only class name.
		Override to write additional subclass-specific properties.
		Don't forget to call super().save()!
		"""
		writer.write(type(self).__name__)
