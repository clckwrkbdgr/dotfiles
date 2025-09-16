from clckwrkbdgr.utils import classfield
from . import entity

class Item(entity.Entity):
	_metainfo_key = 'Items'
	attack = classfield('_attack', 0) # Base attack damage.

class Wearable(object):
	""" Trait for items that can be worn as outfit.
	"""
	protection = classfield('_protection', 0) # Base protection from incoming attacks.
	speed_penalty = classfield('_speed_penalty', 1.0) # Multiplier for every actor's action when equipped.

class Consumable(object):
	""" Trait for consumable items that affect consumer.
	"""
	def consume(self, actor): # pragma: no cover
		""" Should affect actor and return list of produced Events.
		"""
		raise NotImplementedError()

class ItemAtPos(entity.EntityAtPos):
	_entity_type = Item
	@property
	def item(self):
		return self.entity
	@item.setter
	def item(self, value):
		self.entity = value
