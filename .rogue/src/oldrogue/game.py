import functools
from collections import namedtuple
import clckwrkbdgr.collections
from clckwrkbdgr.collections import dotdict
from clckwrkbdgr.utils import get_type_by_name, classfield
from clckwrkbdgr.math import Point, Size, Rect, Matrix
import clckwrkbdgr.math
import logging
trace = logging.getLogger('rogue')
import clckwrkbdgr.logging
from clckwrkbdgr import xdg
from .. import engine

def is_diagonal_movement(point_from, point_to):
	shift = abs(point_to - point_from)
	return shift.x + shift.y > 1

class Version(clckwrkbdgr.collections.Enum):
	auto = clckwrkbdgr.collections.Enum.auto()
	INITIAL = auto()
	ENTER_EXIT = auto()
	LEVELS = auto()
	ITEMS = auto()
	INVENTORY = auto()
	MONSTERS = auto()
	HITPOINTS = auto()
	ITEM_CLASSES = auto()
	WIELDING = auto()
	WEARING = auto()
	JSONPICKLE = auto()

class Event(object):
	@classmethod
	def register(cls, name, fields):
		""" Registers new Event/namedtuple subclass with given name and fields (like for namedtuple).
		Registered class will be available as Event.<name>
		"""
		exec('class {0}(cls, namedtuple(name, fields)): pass'.format(name, repr(name), repr(fields)))
		setattr(cls, name, eval(name))

Event.register('BumpIntoTerrain', 'who pos')
Event.register('BumpIntoMonster', 'who whom')
Event.register('AttackMonster', 'who whom damage')
Event.register('MonsterDied', 'who')
Event.register('MonsterDroppedItem', 'who item')
Event.register('MonsterConsumedItem', 'who item')
Event.register('Unwielding', 'who item')
Event.register('TakingOff', 'who item')
Event.register('Wielding', 'who item')
Event.register('Wearing', 'who item')
Event.register('NotWearable', 'item')
Event.register('NotConsumable', 'item')
Event.register('InventoryFull', 'item')
Event.register('GrabbedItem', 'who item')

class Item(object):
	""" Basic pickable and carryable item. """
	sprite = classfield('_sprite', '*')
	name = classfield('_name', 'mcguffin')
	attack = classfield('_attack', 0)

class Consumable(object):
	def consume_by(self, who): # pragma: no cover
		return NotImplemented

class Wearable(object):
	protection = classfield('_protection', 0)

class Furniture(object):
	""" Any object placed on map that is not a part of the terrain.
	Like stairs, doors, levers etc or even inert objects like statues.
	"""
	class Locked(Exception): # pragma: no cover
		""" Should be thrown when object is locked and requires specific item. """
		def __init__(self, key_item_type):
			self.key_item_type = key_item_type
		def __str__(self):
			return "Locked; required {0} to unlock".format(self.key_item_type)
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'object')

class LevelPassage(Furniture):
	""" Object that allows travel between levels.
	Each passage should be connected to another passage on target level.
	Passages on the same level are differentiated by ID.
	Passage ID can be an arbitrary value.
	"""
	id = classfield('_id', 'enter')
	can_go_down = classfield('_can_go_down', False)
	can_go_up = classfield('_can_go_up', False)
	def __init__(self, level_id, connected_passage): # pragma: no cover
		self.level_id = level_id
		self.connected_passage = connected_passage
	def use(self, who): # pragma: no cover
		""" Additional actions performed before actual travelling.
		By default there are none.
		"""
		pass

class Monster(object):
	def __init__(self):
		self.pos = None
		self.wielding = None
		self.wearing = None
		self.inventory = []
		self.hp = self.max_hp
	sprite = classfield('_sprite', NotImplemented)
	name = classfield('_name', NotImplemented)
	max_hp = classfield('_max_hp', 0)
	base_attack = classfield('_attack', None)
	drops = classfield('_drops', [])
	max_inventory = classfield('_max_inventory', [])
	hostile_to = classfield('_hostile_to', [])
	def is_hostile_to(self, other):
		""" Return True if this monster is hostile towards other monster and can attack it. """
		for monster_class in self.hostile_to:
			if isinstance(other, monster_class):
				return True
		return False
	def heal(self, amount):
		""" Increase health by specified amount, but no more than max_hp. """
		assert amount >= 0
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp
	def has_item(self, item_class, **properties):
		""" Returns True if inventory contains an item of specified class
		with exact values for given properties.
		"""
		for item in self.inventory:
			if not isinstance(item, item_class):
				continue
			for name, expected_value in properties.items():
				if not hasattr(item, name) or getattr(item, name) != expected_value:
					break
			else:
				return True
		return False
	def _unequip(self, item):
		events = []
		if self.wielding == item:
			self.wielding = None
			events.append(Event.Unwielding(self, item))
		if self.wearing == item:
			self.wearing = None
			events.append(Event.TakingOff(self, item))
		return events
	def wield(self, item):
		""" Tries to wield item.
		Returns list of happened events.
		"""
		if item is None:
			events = []
			if self.wielding:
				events.append(Event.Unwielding(self, self.wielding))
			self.wielding = None
			return events
		events = self._unequip(item)
		if self.wielding:
			events.append(Event.Unwielding(self, self.wielding))
			self.wielding = None
		self.wielding = item
		events.append(Event.Wielding(self, item))
		return events
	def wear(self, item):
		""" Tries to wear item.
		Returns list of happened events.
		"""
		if item is None:
			events = []
			if self.wearing:
				events.append(Event.TakingOff(self, self.wearing))
			self.wearing = None
			return events
		if not isinstance(item, Wearable):
			return [Event.NotWearable(item)]
		events = self._unequip(item)
		if self.wearing:
			events.append(Event.TakingOff(self, self.wearing))
			self.wearing = None
		self.wearing = item
		events.append(Event.Wearing(self, item))
		return events
	def drop(self, item):
		""" Tries to drop item from inventory.
		Returns list of happened events.
		"""
		events = self._unequip(item)
		self.inventory.remove(item)
		events.append(Event.MonsterDroppedItem(self, item))
		return events
	def consume(self, item):
		""" Tries to consume item.
		Returns list of happened events.
		"""
		if not isinstance(item, Consumable):
			return [Event.NotConsumable(item)]
		events = self._unequip(item)
		if not item.consume_by(self):
			return events
		self.inventory.remove(item)
		events.append(Event.MonsterConsumedItem(self, item))
		return events
	def get_attack_damage(self):
		""" Final attack damage with all modifiers. """
		if self.base_attack is None:
			return 0
		result = self.base_attack
		if self.wielding:
			result += self.wielding.attack
		return result
	def get_protection(self):
		""" Final protection from damage with all modifiers. """
		if self.wearing:
			return self.wearing.protection
		return 0
	def is_alive(self):
		return self.hp > 0
	def attack(self, other):
		""" Inflicts damage on other actor (considering all modifiers on both actors).
		Returns value of real inflicted damage.
		"""
		damage = max(0, self.get_attack_damage() - other.get_protection())
		other.hp -= damage
		return damage
	def __setstate__(self, data): # pragma: no cover -- TODO
		self.inventory = []
		self.pos = data.pos
		self.inventory = data.inventory
		self.wielding = None
		if 'wielding' in data:
			wielding = data.wielding
			if wielding is not None:
				self.wielding = self.inventory[wielding]
		self.wearing = None
		if 'wearing' in data:
			wearing = data.wearing
			if wearing is not None:
				self.wearing = self.inventory[wearing]
		if data.get('hp'):
			self.hp = data.hp
		else:
			self.hp = self.max_hp
	def __getstate__(self): # pragma: no cover -- TODO
		data = dotdict()
		data._class = self.__class__.__name__
		data.pos = self.pos
		data.inventory = self.inventory
		data.hp = self.hp
		data.wielding = self.inventory.index(self.wielding) if self.wielding else None
		data.wearing = self.inventory.index(self.wearing) if self.wearing else None
		return data

class Room(Rect):
	def __init__(self, topleft, size):
		super(Room, self).__init__(topleft, size)
		self.visited = False
	def __hash__(self):
		return hash( (self.topleft, self.size) )
	def __setstate__(self, data): # pragma: no cover -- TODO
		super(Room, self).__setstate__(data)
		self.visited = data.visited
	def __getstate__(self): # pragma: no cover -- TODO
		data = dotdict(super(Room, self).__getstate__())
		data.visited = self.visited
		return data

class Tunnel(clckwrkbdgr.math.geometry.RectConnection):
	def __init__(self, *args, **kwargs):
		super(Tunnel, self).__init__(*args, **kwargs)
		self.visited = set()
	def __hash__(self):
		return hash( (self.start, self.stop, self.bending_point) )
	def __setstate__(self, data): # pragma: no cover -- TODO
		super(Tunnel, self).__setstate__(data)
		self.visited = set(data.visited)
	def __getstate__(self): # pragma: no cover -- TODO
		data = dotdict(super(Tunnel, self).__getstate__())
		data.visited = list(self.visited)
		return data
	def visit(self, pos, adjacent=True):
		""" Marks cell as visited. If adjacent is True, marks all neighbouring cells too. """
		shifts = [Point(0, 0)]
		if adjacent:
			shifts += [
				Point(-1, 0),
				Point(0, -1),
				Point(+1, 0),
				Point(0, +1),
				]
		for shift in shifts:
			p = pos + shift
			if self.contains(p):
				self.visited.add(p)

class GridRoomMap(object):
	""" Original Rogue-like map with grid of rectangular rooms connected by tunnels.
	Items, monsters, fitment objects are supplied.
	"""
	def __init__(self, level_id=None,
			rooms=None, tunnels=None,
			items=None, monsters=None, objects=None,
			): # pragma: no cover
		self.level_id = level_id
		self.rooms = rooms or Matrix( (3, 3) )
		self.tunnels = tunnels or []
		self.items = items or []
		self.monsters = monsters or []
		self.objects = objects or []
	@functools.lru_cache()
	def room_of(self, pos):
		return next((room for room in self.rooms.data if room.contains(pos, with_border=True)), None)
	@functools.lru_cache()
	def tunnel_of(self, pos):
		return next((tunnel for tunnel in self.tunnels if tunnel.contains(pos)), None)
	@functools.lru_cache()
	def get_tunnels(self, room):
		""" Returns all tunnels connected to the room. """
		tunnels = []
		for tunnel in self.tunnels:
			if room.contains(tunnel.start, with_border=True):
				tunnels.append(tunnel)
			elif room.contains(tunnel.stop, with_border=True):
				tunnels.append(tunnel)
		return tunnels
	@functools.lru_cache()
	def get_tunnel_rooms(self, tunnel):
		""" Returns both rooms that tunnel connects. """
		start_room = next(_ for _ in self.rooms.values() if _.contains(tunnel.start, with_border=True))
		stop_room = next(_ for _ in self.rooms.values() if _.contains(tunnel.stop, with_border=True))
		return start_room, stop_room
	def can_move_to(self, pos, with_tunnels=True, from_pos=None):
		""" Returns True if pos is available for movement.
		If with_tunnels is False, prohibits movements in tunnels and their doors.
		If from_pos is given, considers relative direction and prohibits
		diagonal movement in/from/to tunnels.
		"""
		dest_room = self.room_of(pos)
		if dest_room:
			if dest_room.contains(pos):
				return True
			for tunnel in self.get_tunnels(dest_room):
				if tunnel.contains(pos):
					if from_pos and is_diagonal_movement(from_pos, pos):
						return False
					return True
		if with_tunnels:
			dest_tunnel = self.tunnel_of(pos)
			if dest_tunnel:
				if from_pos and is_diagonal_movement(from_pos, pos):
					return False
				return True
		return False
	def objects_at(self, pos):
		""" Yield objects at pos in reverse order (from top to bottom). """
		for obj_pos, obj in reversed(self.objects):
			if obj_pos == pos:
				yield obj
	def items_at(self, pos):
		""" Yield items at pos in reverse order (from top to bottom). """
		for item_pos, item in reversed(self.items):
			if item_pos == pos:
				yield item
	def monsters_at(self, pos):
		""" Yield monsters at pos in reverse order (from top to bottom). """
		for monster in reversed(self.monsters):
			if monster.pos == pos:
				yield monster
	def rip(self, who):
		""" Processes monster's death (it should be actually not is_alive() for that).
		Drops all items from inventory to the ground at the same pos.
		Yields all dropped items.
		Removes monster from the level.
		"""
		if who.is_alive():
			raise RuntimeError("Trying to bury someone alive: {0}".format(who))
		while who.inventory:
			item = who.inventory.pop()
			self.items.append( (who.pos, item) )
			yield item
		try:
			self.monsters.remove(who)
		except ValueError: # pragma: no cover -- TODO rogue is not stored in the list.
			pass
	def grab_item(self, who, item):
		if len(who.inventory) >= who.max_inventory:
			return [Event.InventoryFull(item)]
		index, = [index for index, (pos, i) in enumerate(self.items) if i == item]
		who.inventory.append(item)
		self.items.pop(index)
		return [Event.GrabbedItem(who, item)]
	def drop_item(self, who, item):
		events = who.drop(item)
		self.items.append( (who.pos, item) )
		return events
	def visit(self, pos):
		""" Marks all objects (rooms, tunnels) related to pos as visited. """
		room = self.room_of(pos)
		if room:
			room.visited = True
			for tunnel in self.get_tunnels(room):
				if room.contains(tunnel.start, with_border=True):
					tunnel.visit(tunnel.start, adjacent=False)
				if room.contains(tunnel.stop, with_border=True):
					tunnel.visit(tunnel.stop, adjacent=False)
		tunnel = self.tunnel_of(pos)
		if tunnel:
			tunnel.visit(pos)

	def __setstate__(self, data): # pragma: no cover -- TODO
		self.rooms = data.rooms
		self.tunnels = data.tunnels
		self.level_id = data.level_id

		self.objects = data.objects
		self.items = data.map_items
		self.monsters = data.monsters
	def __getstate__(self): # pragma: no cover -- TODO
		data = dotdict()
		data.level_id = self.level_id
		data.rooms = self.rooms
		data.tunnels = self.tunnels
		data.objects = self.objects
		data.map_items = []
		for pos, item in self.items:
			data.map_items.append( [pos, item] )
		data.monsters = self.monsters
		return data

class GodMode(object):
	""" God mode options.
	Vision: allows to see everything regardless of obstacles.
	"""
	def __init__(self):
		self.vision = False

class Dungeon(engine.Game):
	""" Set of connected PCG levels with player. """
	GENERATOR = None
	PLAYER_TYPE = None
	def __init__(self):
		super(Dungeon, self).__init__()
		self.levels = {}
		self.current_level_id = None
		self.rogue = self.PLAYER_TYPE()
		self.generator = self.GENERATOR()
		self.god = GodMode()
		self.history = []
	def generate(self): # pragma: no cover -- TODO
		self.go_to_level(0)
		self.rogue.inventory.append(Dagger())
	def load(self, reader): # pragma: no cover -- TODO
		self.levels = data.levels
		self.current_level_id = data.current_level
		self.rogue = data.rogue
		dungeon.history.append(Event.WelcomeBack(dungeon.rogue))
	def save(self, data): # pragma: no cover -- TODO
		data.levels = self.levels
		data.current_level = self.current_level_id
		data.rogue = self.rogue
	@property
	def current_level(self):
		return self.levels[self.current_level_id]
	@property
	def current_room(self):
		return self.current_level.room_of(self.rogue.pos)
	@property
	def current_tunnel(self):
		return self.current_level.tunnel_of(self.rogue.pos)
	def is_finished(self):
		return not self.rogue.is_alive()
	def is_visible(self, obj, additional=None):
		""" Returns true if object (Room, Tunnel, Point) is visible for player.
		Additional data depends on type of primary object.
		Currently only Tunnel Points are considered.
		"""
		if self.god.vision:
			return True
		if isinstance(obj, Room):
			return obj == self.current_room
		if isinstance(obj, Tunnel):
			return additional in obj.visited
		if isinstance(obj, Point):
			for room in self.current_level.rooms.values():
				if room.contains(obj) and self.is_visible(room):
					return True
			for tunnel in self.current_level.tunnels:
				if self.is_visible(tunnel, obj):
					return True
		return False
	def is_remembered(self, obj, additional=None):
		""" Returns true if object (Room, Tunnel, Point) was visible for player at some point and now can be remembered.
		Additional data depends on type of primary object.
		Currently only Tunnel Points are considered.
		"""
		if self.god.vision:
			return True
		if isinstance(obj, Room):
			return obj.visited
		if isinstance(obj, Tunnel):
			return additional in obj.visited
		if isinstance(obj, Point):
			for room in self.current_level.rooms.values():
				if room.contains(obj) and self.is_remembered(room):
					return True
			for tunnel in self.current_level.tunnels:
				if self.is_remembered(tunnel, obj):
					return True
		return False
	def go_to_level(self, level_id, connected_passage='enter'):
		""" Travel to specified level and enter through specified passage.
		If level was not generated yet, it will be generated at this moment.
		"""
		if level_id not in self.levels:
			self.levels[level_id] = self.generator.build_level(level_id)
		stairs = next((pos for pos, obj in reversed(self.levels[level_id].objects) if isinstance(obj, LevelPassage) and obj.id == connected_passage), None)
		assert stairs is not None, "No stairs with id {0}".format(repr(connected_passage))
		self.current_level_id = level_id
		self.rogue.pos = stairs
		self.current_level.visit(self.rogue.pos)
	def use_stairs(self, stairs):
		""" Use level passage object. """
		stairs.use(self.rogue)
		self.go_to_level(stairs.level_id, stairs.connected_passage)
	def move_monster(self, monster, new_pos, with_tunnels=True):
		""" Tries to move monster to a new position.
		May attack hostile other monster there.
		Returns happened events as ordered list of objects:
		- Point: impassable terrain.
		- Monster: other monster is there.
		- int: other monster was attacked and received this damage.
		- Item: other monster dropped an item.
		Empty list means the monster is successfully moved.
		"""
		can_move = self.current_level.can_move_to(new_pos, with_tunnels=with_tunnels, from_pos=monster.pos)
		if not can_move:
			return [Event.BumpIntoTerrain(monster, new_pos)]
		others = [other for other in self.current_level.monsters_at(new_pos) if other != monster]
		if self.rogue.pos == new_pos:
			others.append(self.rogue)
		if not others:
			monster.pos = new_pos
			return []
		hostiles = [other for other in others if monster.is_hostile_to(other)]
		if not hostiles:
			return [Event.BumpIntoMonster(monster, others[0])]
		other = hostiles[0]
		damage = monster.attack(other)
		events = [Event.AttackMonster(monster, other, damage)]
		if not other.is_alive():
			events.append(Event.MonsterDied(other))
			for item in self.current_level.rip(other):
				events.append(Event.MonsterDroppedItem(other, item))
		return events
