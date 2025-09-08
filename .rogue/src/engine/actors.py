from clckwrkbdgr.math import Point, Rect, Size, distance, Direction
from clckwrkbdgr.utils import classfield
from clckwrkbdgr import pcg
from clckwrkbdgr import utils
from . import items
from . import entity

class Actor(entity.Entity):
	""" Basic actor.
	Supports no properties/behaviour except movement.
	"""
	_metainfo_key = 'Actors'
	vision = classfield('_vision', 0) # Radius of field of vision.

	def __init__(self, pos):
		self.pos = Point(pos) if pos else None
		self.action_points = True # TODO should be proper counter for free action points left. Also should save them.
	def __repr__(self):
		return '{0}({1} @{2})'.format(type(self).__name__, self.name, self.pos)

	def has_acted(self):
		""" Returns True if there are no more free action points left. """
		return not self.action_points # TODO should be a number.
	def add_action_points(self, amount=None):
		""" Adds free action points (usually at the start of new turn). """
		self.action_points = True # TODO Should be a number and consider _amount_.
	def spend_action_points(self, amount=None):
		""" Decreases free action points (when some action is performed). """
		self.action_points = False # TODO Should be a number and consider _amount_.
	def apply_auto_effects(self): # pragma: no cover
		""" Apply any internal effects of on-going conditions at the end of current turn,
		like regeneration or poison.
		"""
		pass

	@classmethod
	def load(cls, reader):
		""" Loads basic info about Actor object (class name and pos)
		"""
		return super(Actor, cls).load(reader, _additional_init=lambda r: r.read_point())
	def save(self, writer):
		""" Default implementation writes only class name and position.
		Override to write additional subclass-specific properties.
		Don't forget to call super().save()!
		"""
		super(Actor, self).save(writer)
		writer.write(self.pos)

class Behaviour(object):
	""" Base trait for behavior.
	Monsters that can act should inherit from any kind of Behaviour class.
	"""
	def act(self, game): # pragma: no cover
		""" Custom actions for the actor on the given game state.
		Default implementation does nothing (dummy).
		"""
		pass

class Monster(Actor):
	""" Monster is a perishable Actor (has hp and can be hit)
	and inventory of Items (can carry/drop items).
	"""
	class InventoryFull(RuntimeError): pass
	class ItemNotFit(RuntimeError):
		def __init__(self, required_trait):
			self.required_trait = required_trait

	max_hp = classfield('_max_hp', 1)
	max_inventory = classfield('_max_inventory', 1)
	drops = classfield('_drops', None) # See .fill_drops() for details
	base_attack = classfield('_attack', 0) # Base unarmed attack.
	base_protection = classfield('_protection', 0) # Base protection.
	hostile_to = classfield('_hostile_to', tuple()) # Classes of monsters to be pursue and/or attack.

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

	def _resolve_item(self, item_or_key, remove=False):
		""" Returns real item.
		Item could be a real item object or a key in the inventory.
		Checks that item is present in the inventory.
		If remove=True, additionally removes item from the inventory.
		"""
		if not isinstance(item_or_key, items.Item):
			if remove:
				return self.inventory.pop(item_or_key)
			return self.inventory[item_or_key]
		assert item_or_key in self.inventory
		if remove:
			self.inventory.remove(item_or_key)
			return item_or_key
		return item_or_key

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
	def get_attack_damage(self):
		""" Final attack damage with all modifiers. """
		return self.base_attack
	def get_protection(self):
		""" Final protection from damage with all modifiers. """
		return self.base_protection

	def is_hostile_to(self, other):
		""" Return True if this monster is hostile towards other monster and can attack it. """
		for monster_class in self.hostile_to:
			if isinstance(other, monster_class):
				return True
		return False

	def grab(self, *items):
		""" Adds items to the inventory.
		If total size of inventory will overflow max_inventory,
		does not add any item and raises InventoryFull.
		"""
		if len(self.inventory) + len(items) > self.max_inventory:
			raise self.InventoryFull()
		self.inventory.extend(items)
	def iter_items(self, item_class, **properties):
		""" Iterates over items in the inventory of specified class
		with exact values for given properties.
		"""
		for item in self.inventory:
			if not isinstance(item, item_class):
				continue
			for name, expected_value in properties.items():
				if not hasattr(item, name) or getattr(item, name) != expected_value:
					break
			else:
				yield item
	def find_item(self, item_class, **properties):
		""" Returns first found item from the inventory of specified class
		with exact values for given properties.
		Returns None if no such item is found.
		"""
		return next(self.iter_items(item_class, **properties), None)
	def has_item(self, item_class, **properties):
		""" Returns True if inventory contains an item of specified class
		with exact values for given properties.
		"""
		return bool(self.find_item(item_class, **properties))
	def fill_drops(self, rng):
		""" Generates and adds random items that monsters usually drop upon death.
		Drops is either a list of weighted choices (<weight>, <item type>),
		or a list of such lists. In latter case add several items (one for each sublist).
		Item type may be None - as an option to drop nothing.
		"""
		if not self.drops:
			return
		drops = self.drops
		if drops and drops[0] and not utils.is_collection(drops[0][0]):
			drops = [drops]
		for drop_distribution in drops:
			item_type = pcg.weighted_choices(rng, drop_distribution)[0]
			if item_type is None:
				continue
			self.inventory.append(item_type())
		self._drops = [] # Reset drops for this instance.
	def drop(self, item):
		""" Removes item from inventory and returns ItemAtPos
		with monster's current position.
		Item could be a real item object or a key in the inventory.
		"""
		item = self._resolve_item(item, remove=True)
		return items.ItemAtPos(self.pos, item)
	def drop_all(self):
		""" Drops all inventory (usually in case of death).
		Yields ItemAtPos entries with monster's current position.
		"""
		while self.inventory:
			item = self.inventory.pop()
			yield items.ItemAtPos(self.pos, item)
	def consume(self, item):
		""" Applies effect (by calling item.consume) to the monster.
		Removes item from inventory.
		Returns events produced by item.consume()
		If item is not Consumable, raises ItemNotFit.
		"""
		if not isinstance(item, items.Consumable):
			raise self.ItemNotFit(items.Consumable)
		item = self._resolve_item(item, remove=True)
		return item.consume(self)

class EquippedMonster(Monster):
	""" Monster with ability to equip items:
	arm themselves, wear outfits etc.
	Equipped items are removed from inventory and thus saved separately.
	"""
	class SlotIsTaken(RuntimeError): pass

	def __init__(self, pos):
		super(EquippedMonster, self).__init__(pos)
		self.wielding = None
		self.wearing = None
	def save(self, stream):
		super(EquippedMonster, self).save(stream)
		stream.write(self.wielding, optional=True)
		stream.write(self.wearing, optional=True)
	def load(self, stream):
		super(EquippedMonster, self).load(stream)
		self.wielding = stream.read(items.Item, optional=True)
		self.wearing = stream.read(items.Item, optional=True)

	def get_attack_damage(self):
		""" Final attack damage with all modifiers. """
		result = self.base_attack
		if self.wielding:
			result += self.wielding.attack
		return result
	def get_protection(self):
		""" Final protection from damage with all modifiers. """
		result = self.base_protection
		if self.wearing:
			return self.wearing.protection
		return result

	def wield(self, item):
		""" Wields item from inventory.
		This removes item from the inventory.
		If already wielding something else, SlotIsTaken is raised.
		Item could be a real item object or a key in the inventory.
		"""
		item = self._resolve_item(item)
		if self.wielding:
			raise self.SlotIsTaken()
		self.wielding = self._resolve_item(item, remove=True)
	def unwield(self):
		""" Unwields currently wielded item.
		Appends item back to the inventory.
		Returns the item if some item was actually wielded, or None.
		"""
		if not self.wielding:
			return None
		item, self.wielding = self.wielding, None
		self.inventory.append(item)
		return item
	def wear(self, item):
		""" Wears item from inventory.
		This removes item from the inventory.
		If item is not Wearable, raises ItemNotFit.
		If already wearing something else, SlotIsTaken is raised.
		Item could be a real item object or a key in the inventory.
		"""
		item = self._resolve_item(item)
		if not isinstance(item, items.Wearable):
			raise self.ItemNotFit(items.Wearable)
		if self.wearing:
			raise self.SlotIsTaken()
		self.wearing = self._resolve_item(item, remove=True)
	def take_off(self):
		""" Takes off currently worn item.
		Appends item back to the inventory.
		Returns the item if some item was actually worn, or None.
		"""
		if not self.wearing:
			return None
		item, self.wearing = self.wearing, None
		self.inventory.append(item)
		return item

class Player(Behaviour):
	""" Trait for player character.
	Does nothing in act() due to being controlled by UI input.
	"""
	def act(self, game): # pragma: no cover
		pass

class Neutral(Behaviour):
	""" Trait for neutral non-player character.
	Does nothing on its own.
	"""
	def act(self, game): # pragma: no cover
		pass

class Defensive(Behaviour):
	""" Stands still. Attacks only monsters within melee distance.
	"""
	def act(self, game):
		pos = game.scene.get_global_pos(self)
		close_rect = Rect(pos - Point(1, 1), Size(3, 3))
		for monster in game.scene.iter_actors_in_rect(close_rect):
			if not self.is_hostile_to(monster):
				continue
			game.attack(self, monster)
			break

class Offensive(Behaviour):
	""" Rushes towards any hostile being entered its field of vision
	and attacks.
	"""
	def act(self, game):
		self_pos = game.scene.get_global_pos(self)
		action_range = Rect(
				self_pos - Point(self.vision, self.vision),
				Size(1 + self.vision * 2, 1 + self.vision * 2),
				)

		closest = []
		for monster in game.scene.iter_actors_in_rect(action_range):
			if not self.is_hostile_to(monster):
				continue
			monster_pos = game.scene.get_global_pos(monster)
			closest.append((distance(self_pos, monster_pos), monster))
		if not closest:
			return

		_, target = sorted(closest)[0]
		target_pos = game.scene.get_global_pos(target)

		if distance(self_pos, target_pos) <= 1:
			game.attack(self, target)
			return

		vision = game.scene.make_vision(self)
		vision.visit(self)
		if vision.is_visible(target_pos):
			direction = Direction.from_points(self_pos, target_pos)
			game.move_actor(self, direction)
