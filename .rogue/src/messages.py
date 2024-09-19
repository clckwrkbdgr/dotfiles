class Event(object):
	""" Base class for any game event. """
	pass

class DiscoverEvent(Event):
	""" Something new is discovered on the map! """
	def __init__(self, obj):
		self.obj = obj
	def __str__(self):
		return 'Discovered {0}'.format(str(self.obj))

class AttackEvent(Event):
	""" Attack was performed. """
	def __init__(self, actor, target):
		self.actor = actor
		self.target = target
	def __str__(self):
		return '{0} attacks {1}'.format(str(self.actor), str(self.target))

class HealthEvent(Event):
	""" Health stat has been changed. """
	def __init__(self, target, diff):
		self.target = target
		self.diff = diff
	def __str__(self):
		return '{0} {1:+} hp'.format(str(self.target), self.diff)

class DeathEvent(Event):
	""" Someone's is no more. """
	def __init__(self, target):
		self.target = target
	def __str__(self):
		return '{0} dies'.format(str(self.target))

class MoveEvent(Event):
	""" Location is changed. """
	def __init__(self, actor, dest):
		self.actor = actor
		self.dest = dest
	def __str__(self):
		return '{0} moves to {1}'.format(str(self.actor), self.dest)

class DescendEvent(Event):
	""" Descended to another level. """
	def __init__(self, actor):
		self.actor = actor
	def __str__(self):
		return '{0} descends'.format(self.actor)

class BumpEvent(Event):
	""" Bumps into impenetrable obstacle. """
	def __init__(self, actor, dest):
		self.actor = actor
		self.dest = dest
	def __str__(self):
		return '{0} bumps into {1}'.format(str(self.actor), self.dest)

class GrabItemEvent(Event):
	""" Grabs something from the floor. """
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} grabs {1}'.format(self.actor, self.item)

class DropItemEvent(Event):
	""" Drops something on the floor. """
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} drops {1}'.format(self.actor, self.item)

class ConsumeItemEvent(Event):
	""" Consumes consumable item. """
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} consumes {1}'.format(self.actor, self.item)

class EquipItemEvent(Event):
	""" Equips item. """
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} equips {1}'.format(self.actor, self.item)

class UnequipItemEvent(Event):
	""" Unequips item. """
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} unequips {1}'.format(self.actor, self.item)
