from .utils import Enum

class Behavior(Enum):
	""" PLAYER
	DUMMY
	INERT
	ANGRY
	"""

class Species(object):
	def __init__(self, name, sprite, max_hp):
		self.name = name
		self.sprite = sprite
		self.max_hp = max_hp
	def __str__(self):
		return "{0} {1}hp".format(self.name, self.max_hp)

class Monster(object):
	def __init__(self, species, behavior, pos):
		self.species = species
		self.behavior = behavior
		self.pos = pos
		self.hp = self.species.max_hp
	def __str__(self):
		return "{0} @{1} {2}/{3}hp".format(self.species.name, self.pos, self.hp, self.species.max_hp)
	def is_alive(self):
		return self.hp > 0
	@property
	def name(self):
		return self.species.name
	def __eq__(self, other):
		if not isinstance(other, Monster):
			return False
		return self.species == other.species \
				and self.pos == other.pos \
				and self.hp == other.hp
