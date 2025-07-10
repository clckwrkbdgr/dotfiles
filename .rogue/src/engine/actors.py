from clckwrkbdgr.math import Point
from clckwrkbdgr.utils import classfield
from . import items
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
	""" Monster is a perishable Actor (has hp and can be hit)
	and inventory of Items (can carry/drop items).
	"""
	max_hp = classfield('_max_hp', 1)
	def __init__(self, pos):
		super(Monster, self).__init__(pos)
		self.hp = self.max_hp
		self.inventory = []
	def __repr__(self):
		return '{0}({1} @{2} {3}/{4}hp)'.format(type(self).__name__, self.name, self.pos, self.hp, self.max_hp)
	def save(self, stream):
		super(Monster, self).save(stream)
		stream.write(self.hp)

		stream.write(len(self.inventory))
		for item in self.inventory:
			item.save(stream)
	def load(self, stream):
		self.hp = stream.read(int)

		num_items = stream.read(int)
		for _ in range(num_items):
			item = stream.read(items.Item)
			self.inventory.append(item)
		return self

	def is_alive(self):
		return self.hp > 0
	def affect_health(self, diff):
		""" Increase or decrease health by specified amount, but keeps within ranger [0; max_hp].
		Returns actually applied diff.
		"""
		new_hp = self.hp + diff
		if new_hp < 0:
			new_hp = 0
			diff = new_hp - self.hp
		elif new_hp >= self.max_hp:
			new_hp = self.max_hp
			diff = new_hp - self.hp
		self.hp += diff
		return diff
