from clckwrkbdgr.collections import DocstringEnum as Enum
from .engine import items

class Effect(Enum):
	""" NONE
	HEALING
	"""

class ItemType(object):
	""" Basic fixed stats shared by items of the same kind. """
	def __init__(self, name, sprite, effect):
		self.name = name
		self.sprite = sprite
		self.effect = effect
	def __str__(self):
		return '{0}'.format(self.name)

class Item(items.Item):
	""" Any item that can be picked, carried, stored and used. """
	def __init__(self, item_type):
		self.item_type = item_type
	@property
	def name(self):
		return self.item_type.name
	def __str__(self):
		return self.name
	@classmethod
	def load(cls, reader):
		item_type_name = reader.read()
		item_type = reader.get_meta_info('ITEMS')[item_type_name]
		return cls(item_type)
	def save(self, writer):
		writer.write(self.item_type.name)

class ItemAtPos(object):
	def __init__(self, pos, item):
		self.pos = pos
		self.item = item
	def __str__(self):
		return '{0} @{1}'.format(self.item, self.pos)
	def __eq__(self, item):
		return self.item == item
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
