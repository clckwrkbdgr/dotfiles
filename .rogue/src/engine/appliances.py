from clckwrkbdgr.utils import classfield
from . import entity

class Appliance(entity.Entity):
	_metainfo_key = 'Appliances'
	passable = classfield('_passable', True) # allow free movement through the structure.

class Door(Appliance):
	""" Base for object that can be opened/closed.
	Passability and sprite depend on the state.
	At least closed_sprite must be defined.
	"""
	opened_sprite = classfield('_opened_sprite', None)
	closed_sprite = classfield('_closed_sprite', None)
	def __init__(self, closed=False):
		self._closed = closed
	def load(self, stream):
		self._closed = bool(stream.read(int))
	def save(self, stream):
		super(Door, self).save(stream)
		stream.write(self._closed)
	@property
	def passable(self):
		return not self._closed
	@property
	def sprite(self):
		if not self._closed and self.opened_sprite:
			return self.opened_sprite
		return self.closed_sprite
	def is_closed(self):
		return self._closed
	def open(self):
		self._closed = False
	def close(self):
		self._closed = True
	def toggle(self):
		self._closed = not self._closed

class LockedObject(object):
	class Locked(Exception):
		""" Should be thrown when passage is locked
		and requires item of specific type to travel through.
		"""
		def __init__(self, key_item_type):
			self.key_item_type = key_item_type
		def __str__(self):
			return "Locked; required {0} to unlock".format(self.key_item_type.__name__)

	unlocking_item = classfield('_unlocking_item', None) # Type of item that unlocks appliance; by default (None) allows usage unconditionally.
	def check_lock(self, user=None, lock_id=None):
		if not self.unlocking_item:
			return
		if not (user and user.has_item(self.unlocking_item)):
			raise self.Locked(self.unlocking_item)

class LockedDoor(Door, LockedObject):
	def __init__(self, closed=False, locked=False):
		self._closed = closed
		self._locked = locked
	def load(self, stream):
		super(LockedDoor, self).load(stream)
		self._locked = bool(stream.read(int))
	def save(self, stream):
		super(LockedDoor, self).save(stream)
		stream.write(self._locked)
	def is_locked(self):
		return self._locked
	def lock(self, user):
		self.check_lock(user)
		self._locked = True
	def unlock(self, user):
		self.check_lock(user)
		self._locked = False
	def open(self):
		if self._locked:
			self.check_lock()
		super(LockedDoor, self).open()
	def close(self):
		if self._locked:
			self.check_lock()
		super(LockedDoor, self).close()
	def toggle(self):
		if self._locked:
			self.check_lock()
		super(LockedDoor, self).toggle()

class LevelPassage(Appliance, LockedObject):
	""" Object that allows travel between levels.
	Each passage should be connected to another passage on target level.
	Passages on the same level are differentiated by ID.
	Passage ID can be an arbitrary value.
	"""

	id = classfield('_id', 'enter') # ID of passage that can be used as a target during travelling.
	can_go_down = classfield('_can_go_down', False)
	can_go_up = classfield('_can_go_up', False)

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
		self.check_lock(user)
		return self.level_id, self.connected_passage

class ObjectAtPos(entity.EntityAtPos):
	_entity_type = Appliance
	@property
	def obj(self):
		return self.entity
	@obj.setter
	def obj(self, value):
		self.entity = value
