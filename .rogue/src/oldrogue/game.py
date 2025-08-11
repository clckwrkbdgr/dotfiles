import functools
from collections import namedtuple
import clckwrkbdgr.collections
from clckwrkbdgr.collections import dotdict
from clckwrkbdgr.utils import get_type_by_name, classfield
from clckwrkbdgr.math import Point, Size, Rect, Matrix
import clckwrkbdgr.math
from ..engine import math
import logging
trace = logging.getLogger('rogue')
import clckwrkbdgr.logging
from clckwrkbdgr import xdg
from .. import engine
from ..engine import events, scene
from ..engine import actors, items, appliances
from ..engine.items import Item, Wearable

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

class Event:
	class BumpIntoTerrain(events.Event): FIELDS = 'who pos'
	class BumpIntoMonster(events.Event): FIELDS = 'who whom'
	class AttackMonster(events.Event): FIELDS = 'who whom damage'
	class MonsterDied(events.Event): FIELDS = 'who'
	class MonsterDroppedItem(events.Event): FIELDS = 'who item'
	class MonsterConsumedItem(events.Event): FIELDS = 'who item'
	class Unwielding(events.Event): FIELDS = 'who item'
	class TakingOff(events.Event): FIELDS = 'who item'
	class Wielding(events.Event): FIELDS = 'who item'
	class Wearing(events.Event): FIELDS = 'who item'
	class NotWearable(events.Event): FIELDS = 'item'
	class NotConsumable(events.Event): FIELDS = 'item'
	class InventoryFull(events.Event): FIELDS = 'item'
	class GrabbedItem(events.Event): FIELDS = 'who item'
	class CannotReachCeiling(events.Event): FIELDS = ''
	class GoingUp(events.Event): FIELDS = ''
	class GoingDown(events.Event): FIELDS = ''
	class CannotDig(events.Event): FIELDS = ''
	class NeedKey(events.Event): FIELDS = 'key'
	class NothingToPickUp(events.Event): FIELDS = ''

class Player(actors.EquippedMonster):
	_name = 'player'

class Scene(scene.Scene):
	""" Original Rogue-like map with grid of rectangular rooms connected by tunnels.
	Items, monsters, fitment objects are supplied.
	"""
	Room = Rect
	Tunnel = clckwrkbdgr.math.geometry.RectConnection

	def __init__(self, size=None,
			rooms=None, tunnels=None,
			items=None, monsters=None, objects=None,
			): # pragma: no cover
		self.size = size
		self.rooms = rooms or Matrix( (3, 3) )
		self.tunnels = tunnels or []
		self.items = items or []
		self.monsters = monsters or []
		self.objects = objects or []
	def valid(self, pos): # pragma: no cover -- TODO
		return 0 <= pos.x < self.size.width and 0 <= pos.y < self.size.height
	@functools.lru_cache()
	def room_of(self, pos):
		return next((room for room in self.rooms.data if room.contains(pos, with_border=True)), None)
	@functools.lru_cache()
	def tunnel_of(self, pos):
		return next((tunnel for tunnel in self.tunnels if tunnel.contains(pos)), None)
	@functools.lru_cache()
	def index_room_of(self, pos):
		return next((key for key in self.rooms.keys() if self.rooms.cell(key).contains(pos, with_border=True)), None)
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
					if from_pos and math.is_diagonal(from_pos - pos):
						return False
					return True
		if with_tunnels:
			dest_tunnel = self.tunnel_of(pos)
			if dest_tunnel:
				if from_pos and math.is_diagonal(from_pos - pos):
					return False
				return True
		return False
	def get_cell_info(self, pos): # pragma: no cover -- TODO
		terrain = []
		for room in self.rooms.values():
			terrain.append((room.top, room.left, "+"))
			terrain.append((room.bottom, room.left, "+"))
			terrain.append((room.top, room.right, "+"))
			terrain.append((room.bottom, room.right, "+"))
			for x in range(room.left+1, room.right):
				terrain.append((room.top, x, "-"))
				terrain.append((room.bottom, x, "-"))
			for y in range(room.top+1, room.bottom):
				terrain.append((y, room.left, "|"))
				terrain.append((y, room.right, "|"))
			for y in range(room.top+1, room.bottom):
				for x in range(room.left+1, room.right):
					terrain.append((y, x, (".", ' ')))
		for tunnel in self.tunnels:
			for cell in tunnel.iter_points():
				terrain.append((cell.y, cell.x, "#"))
			terrain.append((tunnel.start.y, tunnel.start.x, "+"))
			terrain.append((tunnel.stop.y, tunnel.stop.x, "+"))
		pos = Point(pos)
		Mock_Terrain = namedtuple('Mock_Terrain', 'sprite')
		Mock_Sprite = namedtuple('Mock_Sprite', 'sprite')
		return (
				next(Mock_Terrain(Mock_Sprite(s)) for (y, x, s) in terrain if pos.x == x and pos.y == y),
				list(self.iter_appliances_at(pos)),
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)

	def __setstate__(self, data): # pragma: no cover -- TODO
		self.rooms = data.rooms
		self.tunnels = data.tunnels

		self.objects = data.objects
		self.items = data.map_items
		self.monsters = data.monsters
	def __getstate__(self): # pragma: no cover -- TODO
		data = dotdict()
		data.rooms = self.rooms
		data.tunnels = self.tunnels
		data.objects = self.objects
		data.map_items = []
		for pos, item in self.items:
			data.map_items.append( [pos, item] )
		data.monsters = self.monsters
		return data

	@property
	def current_room(self):
		return self.room_of(self.get_player().pos)
	@property
	def current_tunnel(self):
		return self.tunnel_of(self.get_player().pos)
	def iter_cells(self, view_rect):
		trace.debug(list(self.rooms.keys()))
		terrain = []
		for room in self.rooms.values():
			terrain.append((room.top, room.top, "+"))
			terrain.append((room.top, room.left, "+"))
			terrain.append((room.bottom, room.left, "+"))
			terrain.append((room.top, room.right, "+"))
			terrain.append((room.bottom, room.right, "+"))
			for x in range(room.left+1, room.right):
				terrain.append((room.top, x, "-"))
				terrain.append((room.bottom, x, "-"))
			for y in range(room.top+1, room.bottom):
				terrain.append((y, room.left, "|"))
				terrain.append((y, room.right, "|"))
			for y in range(room.top+1, room.bottom):
				for x in range(room.left+1, room.right):
					terrain.append((y, x, ".")) # , ' ')))
		for tunnel in self.tunnels:
			for cell in tunnel.iter_points():
				terrain.append((cell.y, cell.x, "#"))
			terrain.append((tunnel.start.y, tunnel.start.x, "+"))
			terrain.append((tunnel.stop.y, tunnel.stop.x, "+"))

		Mock_Terrain = namedtuple('Mock_Terrain', 'sprite')
		Mock_Sprite = namedtuple('Mock_Sprite', 'sprite')
		for y, x, sprite in terrain:
			sprite = Mock_Terrain(Mock_Sprite(sprite))
			pos = Point(x, y)
			objects = list(self.iter_appliances_at(pos))
			items = list(self.iter_items_at(pos))
			monsters = list(self.iter_actors_at(pos, with_player=True))
			yield pos, (sprite, objects, items, monsters)
	def iter_items_at(self, pos):
		""" Yield items at pos in reverse order (from top to bottom). """
		for item_pos, item in reversed(self.items):
			if item_pos == pos:
				yield item
	def iter_actors_at(self, pos, with_player=False):
		""" Yield monsters at pos in reverse order (from top to bottom). """
		for monster in reversed(self.monsters):
			if not with_player and isinstance(monster, Player):
				continue
			if monster.pos == pos:
				yield monster
	def iter_appliances_at(self, pos):
		""" Yield objects at pos in reverse order (from top to bottom). """
		for obj_pos, obj in reversed(self.objects):
			if obj_pos == pos:
				yield obj
	def get_player(self):
		return next((monster for monster in self.monsters if isinstance(monster, Player)), None)
	def iter_active_monsters(self):
		return self.monsters

class Dungeon(engine.Game):
	""" Set of connected PCG levels with player. """
	GENERATOR = None
	PLAYER_TYPE = None
	def __init__(self):
		super(Dungeon, self).__init__()
		self.levels = {}
		self.visited_rooms = {}
		self.visited_tunnels = {}
		self.current_level_id = None
		self.generator = self.GENERATOR()
	def generate(self): # pragma: no cover -- TODO
		rogue = self.PLAYER_TYPE()
		rogue.grab(Dagger())
		self.go_to_level(rogue, 0)
	def load(self, reader): # pragma: no cover -- TODO
		self.levels = data.levels
		self.visited_rooms = data.visited_rooms
		self.visited_tunnels = data.visited_tunnels
		self.current_level_id = data.current_level
		self.scene = self.levels[self.current_level_id]
		self.fire_event(Event.WelcomeBack(dungeon.scene.get_player()))
	def save(self, data): # pragma: no cover -- TODO
		data.levels = self.levels
		data.visited_rooms = self.visited_rooms
		data.visited_tunnels = self.visited_tunnels
		data.current_level = self.current_level_id
	def go_to_level(self, monster, level_id, connected_passage='enter'):
		""" Travel to specified level and enter through specified passage.
		If level was not generated yet, it will be generated at this moment.
		"""
		if self.current_level_id is not None:
			self.scene.monsters.remove(monster)
		if level_id not in self.levels:
			self.levels[level_id] = self.generator.build_level(level_id)
			self.visited_rooms[level_id] = Matrix((3, 3), False)
			self.visited_tunnels[level_id] = [set() for tunnel in self.levels[level_id].tunnels]
		stairs = next((pos for pos, obj in reversed(self.levels[level_id].objects) if isinstance(obj, appliances.LevelPassage) and obj.id == connected_passage), None)
		assert stairs is not None, "No stairs with id {0}".format(repr(connected_passage))
		self.current_level_id = level_id
		self.scene = self.levels[self.current_level_id]

		self.scene.monsters.append(monster)
		monster.pos = stairs
		self.visit(monster.pos)
	def use_stairs(self, monster, stairs):
		""" Use level passage object. """
		try:
			stairs.use(monster)
			self.go_to_level(monster, stairs.level_id, stairs.connected_passage)
			return True
		except appliances.LevelPassage.Locked as e:
			self.fire_event(Event.NeedKey(e.key_item_type))
			return False
	def rip(self, who):
		""" Processes monster's death (it should be actually not is_alive() for that).
		Drops all items from inventory to the ground at the same pos.
		Yields all dropped items.
		Removes monster from the level.
		"""
		if who.is_alive():
			raise RuntimeError("Trying to bury someone alive: {0}".format(who))
		for item in who.drop_all():
			self.scene.items.append(item)
			yield item.item
		try:
			self.scene.monsters.remove(who)
		except ValueError: # pragma: no cover -- TODO rogue is not stored in the list.
			pass
	def grab_item(self, who, item):
		index, = [index for index, (pos, i) in enumerate(self.scene.items) if i == item]
		try:
			who.grab(item)
			self.scene.items.pop(index)
			self.fire_event(Event.GrabbedItem(who, item))
		except actors.EquippedMonster.InventoryFull:
			self.fire_event(Event.InventoryFull(item))
	def consume_item(self, actor, item):
		""" Tries to consume item.
		Returns list of happened events.
		"""
		try:
			events = [Event.MonsterConsumedItem(actor, item)]
			events += actor.consume(item)
			for _ in events:
				self.fire_event(_)
		except actor.ItemNotFit as e:
			return self.fire_event(Event.NotConsumable(item))
	def drop_item(self, who, item):
		item = who.drop(item)
		self.scene.items.append(item)
		self.fire_event(Event.MonsterDroppedItem(who, item.item))
	def wield_item(self, who, item):
		try:
			who.wield(item)
		except actors.EquippedMonster.SlotIsTaken:
			old_item = who.unwield()
			self.fire_event(Event.Unwielding(who, old_item))
			who.wield(item)
		self.fire_event(Event.Wielding(who, item))
	def wear_item(self, who, item):
		try:
			who.wear(item)
		except actors.EquippedMonster.ItemNotFit as e:
			self.fire_event(Event.NotWearable(item))
			return
		except actors.EquippedMonster.SlotIsTaken:
			old_item = who.take_off()
			self.fire_event(Event.TakingOff(who, old_item))
			who.wear(item)
		self.fire_event(Event.Wearing(who, item))
	def move_actor(self, monster, shift):
		""" Tries to move monster to a new position.
		May attack hostile other monster there.
		Returns happened events as ordered list of objects:
		- Point: impassable terrain.
		- Monster: other monster is there.
		- int: other monster was attacked and received this damage.
		- Item: other monster dropped an item.
		Empty list means the monster is successfully moved.
		"""
		with_tunnels = (monster == self.scene.get_player())
		new_pos = monster.pos + shift
		can_move = self.scene.can_move_to(new_pos, with_tunnels=with_tunnels, from_pos=monster.pos)
		if not can_move:
			self.fire_event(Event.BumpIntoTerrain(monster, new_pos))
			return
		others = [other for other in self.scene.iter_actors_at(new_pos, with_player=True) if other != monster]
		if not others:
			monster.spend_action_points()
			monster.pos = new_pos
			return
		hostiles = [other for other in others if monster.is_hostile_to(other)]
		if not hostiles:
			monster.spend_action_points()
			self.fire_event(Event.BumpIntoMonster(monster, others[0]))
			return
		other = hostiles[0]
		damage = max(0, monster.get_attack_damage() - other.get_protection())
		other.affect_health(-damage)
		self.fire_event(Event.AttackMonster(monster, other, damage))
		if not other.is_alive():
			self.fire_event(Event.MonsterDied(other))
			for item in self.rip(other):
				self.fire_event(Event.MonsterDroppedItem(other, item))
		monster.spend_action_points()
	def is_visible(self, obj, additional=None):
		""" Returns true if object (Room, Tunnel, Point) is visible for player.
		Additional data depends on type of primary object.
		Currently only Tunnel Points are considered.
		"""
		if self.god.vision:
			return True
		if isinstance(obj, Scene.Room):
			return obj == self.scene.current_room
		if isinstance(obj, Scene.Tunnel):
			tunnel_visited = self.scene.tunnels.index(obj)
			tunnel_visited = self.visited_tunnels[self.current_level_id][tunnel_visited]
			return additional in tunnel_visited
		if isinstance(obj, Point):
			for room in self.scene.rooms.values():
				if room.contains(obj, with_border=True) and self.is_visible(room):
					return True
			for tunnel in self.scene.tunnels:
				if self.is_visible(tunnel, obj):
					return True
		return False
	def actor_sees_player(self, actor):
		if not self.scene.current_room: # pragma: no cover -- TODO
			return False
		sees_rogue = self.scene.current_room.contains(actor.pos)
		return sees_rogue
	def is_visited(self, obj, additional=None):
		""" Returns true if object (Room, Tunnel, Point) was visible for player at some point and now can be remembered.
		Additional data depends on type of primary object.
		Currently only Tunnel Points are considered.
		"""
		if self.god.vision:
			return True
		if isinstance(obj, Scene.Room):
			room_index = self.scene.index_room_of(obj.topleft)
			return self.visited_rooms[self.current_level_id].cell(room_index)
		if isinstance(obj, Scene.Tunnel):
			tunnel_visited = self.scene.tunnels.index(obj)
			tunnel_visited = self.visited_tunnels[self.current_level_id][tunnel_visited]
			return additional in tunnel_visited
		if isinstance(obj, Point):
			for room in self.scene.rooms.values():
				if room.contains(obj, with_border=True) and self.is_visited(room):
					return True
			for tunnel in self.scene.tunnels:
				if self.is_visited(tunnel, obj): # pragma: no covered -- TODO
					return True
		return False
	def visit_tunnel(self, tunnel, pos, adjacent=True):
		""" Marks cell as visited. If adjacent is True, marks all neighbouring cells too. """
		shifts = [Point(0, 0)]
		if adjacent:
			shifts += [
				Point(-1, 0),
				Point(0, -1),
				Point(+1, 0),
				Point(0, +1),
				]
		tunnel_visited = self.scene.tunnels.index(tunnel)
		tunnel_visited = self.visited_tunnels[self.current_level_id][tunnel_visited]
		for shift in shifts:
			p = pos + shift
			if tunnel.contains(p):
				tunnel_visited.add(p)
	def visit(self, pos):
		""" Marks all objects (rooms, tunnels) related to pos as visited. """
		room = self.scene.room_of(pos)
		if room:
			room_index = self.scene.index_room_of(pos)
			self.visited_rooms[self.current_level_id].set_cell(room_index, True)
			for tunnel in self.scene.get_tunnels(room):
				if room.contains(tunnel.start, with_border=True):
					self.visit_tunnel(tunnel, tunnel.start, adjacent=False)
				if room.contains(tunnel.stop, with_border=True):
					self.visit_tunnel(tunnel, tunnel.stop, adjacent=False)
		tunnel = self.scene.tunnel_of(pos)
		if tunnel:
			self.visit_tunnel(tunnel, pos)
	def descend(self, actor):
		dungeon = self
		stairs_here = next(iter(filter(lambda obj: isinstance(obj, appliances.LevelPassage) and obj.can_go_down, dungeon.scene.iter_appliances_at(actor.pos))), None)
		if not stairs_here:
			dungeon.fire_event(Event.CannotDig())
			return False
		if not dungeon.use_stairs(actor, stairs_here):
			return False
		dungeon.fire_event(Event.GoingDown())
		return True
	def ascend(self, actor):
		dungeon = self
		stairs_here = next(iter(filter(lambda obj: isinstance(obj, appliances.LevelPassage) and obj.can_go_up, dungeon.scene.iter_appliances_at(actor.pos))), None)
		if not stairs_here:
			dungeon.fire_event(Event.CannotReachCeiling())
			return False
		if not dungeon.use_stairs(actor, stairs_here):
			return False
		dungeon.fire_event(Event.GoingUp())
		return True
	def grab_here(self, actor):
		dungeon = self
		item_here = next( (index for index, (pos, item) in enumerate(reversed(dungeon.scene.items)) if pos == actor.pos), None)
		trace.debug("Items: {0}".format(dungeon.scene.items))
		trace.debug("Rogue: {0}".format(actor.pos))
		trace.debug("Items here: {0}".format([(index, pos, item) for index, (pos, item) in enumerate(reversed(dungeon.scene.items)) if pos == actor.pos]))
		trace.debug("Item here: {0}".format(item_here))
		if item_here is not None:
			item_here = len(dungeon.scene.items) - 1 - item_here # Index is from reversed list.
			trace.debug("Unreversed item here: {0}".format(item_here))
			_, item = dungeon.scene.items[item_here]
			dungeon.grab_item(actor, item)
			actor.spend_action_points()
		else:
			dungeon.fire_event(Event.NothingToPickUp())
	def move_by(self, actor, shift):
		dungeon = self
		dungeon.move_actor(actor, shift)
		dungeon.visit(actor.pos)
