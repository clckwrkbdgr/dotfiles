from .utils import Enum

class Effect(Enum):
	""" NONE
	HEALING
	"""

class ItemType(object):
	def __init__(self, name, sprite, effect):
		self.name = name
		self.sprite = sprite
		self.effect = effect
	def __str__(self):
		return '{0}'.format(self.name)

class Item(object):
	def __init__(self, item_type, pos):
		self.item_type = item_type
		self.pos = pos
	@property
	def name(self):
		return self.item_type.name
	def __str__(self):
		return '{0} @{1}'.format(self.name, self.pos)
