from clckwrkbdgr.collections import DocstringEnum as Enum
from .engine import items
from .engine.items import ItemAtPos

class Effect(Enum):
	""" NONE
	HEALING
	"""

class ItemType(items.Item):
	""" Basic fixed stats shared by items of the same kind. """
	name = NotImplemented
	sprite = NotImplemented
	effect = Effect.NONE

class Item(ItemType):
	""" Any item that can be picked, carried, stored and used. """
	def __init__(self):
		self.item_type = self
	def __str__(self):
		return self.name
	@classmethod
	def load(cls, reader):
		item_type_name = reader.read()
		item_type = reader.get_meta_info('ITEMS')[item_type_name]
		return item_type()
	def save(self, writer):
		writer.write(type(self.item_type).__name__)
