from clckwrkbdgr.utils import classfield
from . import entity

class Appliance(entity.Entity):
	_metainfo_key = 'Appliances'
	passable = classfield('_passable', True) # allow free movement through the structure.

class LevelPassage(Appliance):
	""" Object that allows travel between levels.
	Each passage should be connected to another passage on target level.
	Passages on the same level are differentiated by ID.
	Passage ID can be an arbitrary value.
	"""
	class Locked(Exception):
		""" Should be thrown when passage is locked
		and requires item of specific type to travel through.
		"""
		def __init__(self, key_item_type):
			self.key_item_type = key_item_type
		def __str__(self):
			return "Locked; required {0} to unlock".format(self.key_item_type.__name__)

	id = classfield('_id', 'enter') # ID of passage that can be used as a target during travelling.
	can_go_down = classfield('_can_go_down', False)
	can_go_up = classfield('_can_go_up', False)
	unlocking_item = classfield('_unlocking_item', None) # Type of item that unlocks travel; by default (None) allows travel unconditionally.

	def __init__(self, level_id=None, connected_passage=None):
		""" Creates level passage linked to specified level/passage. """
		self.level_id = level_id
		self.connected_passage = connected_passage
	def load(self, stream):
		self.level_id = stream.read()
		self.connected_passage = stream.read()
	def save(self, stream):
		super(LevelPassage, self).save(stream)
		stream.write(self.level_id)
		stream.write(self.connected_passage)
	def use(self, user):
		""" Returns travelling coordinates in form of tuple (dest level, arrival passage id).
		If passage requires item to unlock, checks user's inventory beforehand
		and throws Locked() if item is missing.
		"""
		if self.unlocking_item:
			if not user.has_item(self.unlocking_item):
				raise self.Locked(self.unlocking_item)
		return self.level_id, self.connected_passage

class ObjectAtPos(entity.EntityAtPos):
	_entity_type = Appliance
	@property
	def obj(self):
		return self.entity
	@obj.setter
	def obj(self, value):
		self.entity = value
