from .engine import items
from .engine.items import ItemAtPos

class Item(items.Item):
	""" Any item that can be picked, carried, stored and used. """
	@classmethod
	def load(cls, reader):
		item_type_name = reader.read()
		item_type = reader.get_meta_info('ITEMS')[item_type_name]
		return item_type()
	def save(self, writer):
		writer.write(type(self).__name__)

class Consumable(object):
	def apply_effect(self, game, monster): # pragma: no cover
		raise NotImplementedError()
