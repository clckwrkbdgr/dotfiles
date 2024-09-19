from .defs import *
from . import pcg
from .pcg import RNG
from . import math
from .math import Point, Matrix, Size
from . import messages
from .system.logging import Log
from .ui import Action
from . import monsters, items, terrain

class Direction(Enum):
	""" NONE
	UP_LEFT
	UP
	UP_RIGHT
	LEFT
	RIGHT
	DOWN_LEFT
	DOWN
	DOWN_RIGHT
	"""

class Game(object):
	""" Main game object.

	Override definitions for content:
	- BUILDERS: list of Builder classes to build maps.
	- SETTLERS: list of Settler classes to populate them.
	- TERRAIN: dict, registry of Terrain classes by their IDs used in Builders.
	- SPECIES: dict, registry of Species classes by their IDs used in Settlers.
	- ITEMS: dict, registry of Item classes by their IDs used in Settlers.
	"""

	class AutoMovementStopped(BaseException):
		""" Raised when current automovement mode was stopped. """
		pass

	BUILDERS = None
	SETTLERS = None
	TERRAIN = None
	SPECIES = None
	ITEMS = None

	SHIFT = {
			Direction.LEFT : Point(-1,  0),
			Direction.DOWN : Point( 0, +1),
			Direction.UP : Point( 0, -1),
			Direction.RIGHT : Point(+1,  0),
			Direction.UP_LEFT : Point(-1, -1),
			Direction.UP_RIGHT : Point(+1, -1),
			Direction.DOWN_LEFT : Point(-1, +1),
			Direction.DOWN_RIGHT : Point(+1, +1),
			}

	def __init__(self, rng_seed=None, dummy=False, builders=None, settlers=None, load_from_reader=None):
		""" Creates game instance and optionally generate new world.
		Custom rng_seed may be used for PCG.
		If dummy = True, does not automatically generate or load game, just create empty object.
		Optional builders/settlers may be passed to override default class variables.
		If load_from_reader is given, it should be a Reader class, from which game is loaded.
		Otherwise new game is generated.
		"""
		self.builders = builders or self.BUILDERS
		self.settlers = settlers or self.SETTLERS
		self.rng = RNG(rng_seed)
		self.god = God()
		self.field_of_view = math.FieldOfView(10)
		self.autoexploring = False
		self.movement_queue = []
		self.monsters = []
		self.items = []
		self.visible_monsters = []
		self.visible_items = []
		self.events = []
		if dummy:
			return
		if load_from_reader:
			self.load(load_from_reader)
		else:
			self.build_new_strata()
	def load(self, reader):
		""" Loads game from reader. """
		if reader.version > Version.PERSISTENT_RNG:
			self.rng = RNG(reader.read_int())

		legacy_player = None
		if reader.version <= Version.MONSTERS:
			legacy_player = monsters.Monster(self.SPECIES['player'], pcg.settlers.Behavior.PLAYER, reader.read_point())
		self.exit_pos = reader.read_point()
		self.remembered_exit = reader.read_bool()

		reader.set_meta_info('ITEMS', self.ITEMS)
		reader.set_meta_info('SPECIES', self.SPECIES)
		reader.set_meta_info('TERRAIN', self.TERRAIN)
		self.strata = reader.read_matrix(terrain.Cell)
		if legacy_player:
			self.monsters.append(legacy_player)
		if reader.version > Version.MONSTERS:
			self.monsters.extend(reader.read_list(monsters.Monster))
		if reader.version > Version.ITEMS:
			self.items.extend(reader.read_list(items.Item))

		self.update_vision()
		Log.debug('Loaded.')
		Log.debug(repr(self.strata))
		Log.debug('Player: {0}'.format(self.get_player()))
	def save(self, writer):
		""" Saves game using writer. """
		writer.write(self.rng.value)
		writer.write(self.exit_pos)
		writer.write(self.remembered_exit)
		writer.write(self.strata)
		writer.write(self.monsters)
		writer.write(self.items)
	def main_loop(self, ui):
		""" Main entry point for the game.
		Performs main event/action loop, redraws UI.
		Exits when user decided to exit or when player is dead.
		"""
		Log.debug('Starting playing...')
		self.player_turn = True
		while True:
			ui.redraw(self)
			if not self.get_player():
				break
			if not self._perform_player_actions(ui):
				break
			if not self.player_turn:
				for monster in self.monsters:
					if monster.behavior == monsters.Behavior.PLAYER:
						continue
					self._perform_monster_actions(monster)
				self.player_turn = True
		return self.get_player() and self.get_player().is_alive()
	def _perform_player_actions(self, ui):
		""" Controller for player character (via UI). """
		try:
			if self.perform_automovement():
				if ui.user_interrupted():
					self.stop_automovement()
				return True
		except Game.AutoMovementStopped:
			return True

		action, action_data = ui.user_action(self)
		self.clear_event() # If we acted - we've seen all the events.
		if action == Action.NONE:
			pass
		elif action == Action.EXIT:
			return False
		elif action == Action.SUICIDE:
			self.affect_health(self.get_player(), -self.get_player().hp)
			self.player_turn = False
		elif action == Action.WALK_TO:
			self.walk_to(action_data)
		elif action == Action.AUTOEXPLORE:
			self.start_autoexploring()
		elif action == Action.GOD_TOGGLE_VISION:
			self.god.vision = not self.god.vision
		elif action == Action.GOD_TOGGLE_NOCLIP:
			self.god.noclip = not self.god.noclip
		elif action == Action.DESCEND:
			self.descend()
		elif action == Action.MOVE:
			self.move(self.get_player(), action_data)
			self.player_turn = False
		elif action == Action.GRAB:
			self.grab_item_at(self.get_player(), action_data)
			self.player_turn = False
		elif action == Action.CONSUME:
			self.consume_item(self.get_player(), action_data)
			self.player_turn = False
		elif action == Action.DROP:
			self.drop_item(self.get_player(), action_data)
			self.player_turn = False
		elif action == Action.WIELD:
			self.wield_item(self.get_player(), action_data)
			self.player_turn = False
		elif action == Action.UNWIELD:
			self.unwield_item(self.get_player())
			self.player_turn = False
		elif action == Action.WAIT:
			self.player_turn = False
		return True
	def _perform_monster_actions(self, monster):
		""" Controller for monster actions (depends on behavior). """
		if monster.behavior == monsters.Behavior.DUMMY:
			pass
		elif monster.behavior == monsters.Behavior.INERT:
			if self.get_player():
				if math.distance(monster.pos, self.get_player().pos) == 1:
					self.attack(monster, self.get_player())
		elif monster.behavior == monsters.Behavior.ANGRY:
			if self.get_player():
				if math.distance(monster.pos, self.get_player().pos) == 1:
					self.attack(monster, self.get_player())
				elif math.distance(monster.pos, self.get_player().pos) <= monster.species.vision:
					is_transparent = lambda p: self.is_transparent_to_monster(p, monster)
					if math.in_line_of_sight(monster.pos, self.get_player().pos, is_transparent):
						direction = self.get_direction(monster.pos, self.get_player().pos)
						self.move(monster, direction)
	@classmethod
	def get_direction(cls, start, target):
		""" Returns vector from start to target as a Direction value. """
		shift = target - start
		shift = Point(
				shift.x // abs(shift.x) if shift.x else 0,
				shift.y // abs(shift.y) if shift.y else 0,
				)
		return next((k for k,v in cls.SHIFT.items() if v == shift), None)
	def get_viewport(self):
		""" Returns current viewport size (for UI purposes). """
		return self.strata.size
	def tostring(self, with_fov=False):
		""" Creates string representation of the current viewport.
		If with_fov=True, considers transparency/lighting, otherwise everything is visible.
		"""
		size = self.get_viewport()
		result = ""
		if not with_fov:
			old_god_vision = self.god.vision
			self.god.vision = True
		for y in range(size.height):
			for x in range(size.width):
				result += self.get_sprite(x, y) or ' '
			result += "\n"
		if not with_fov:
			self.god.vision = old_god_vision
		return result
	def get_sprite(self, x, y):
		""" Returns top sprite at the given position. """
		monster = self.find_monster(x, y)
		if monster:
			if self.field_of_view.is_visible(x, y) or self.god.vision:
				return monster.species.sprite
		item = self.find_item(x, y)
		if item:
			if self.field_of_view.is_visible(x, y) or self.god.vision:
				return item.item_type.sprite
		if self.exit_pos.x == x and self.exit_pos.y == y:
			if self.god.vision or self.remembered_exit or self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
				return '>'

		cell = self.strata.cell(x, y)
		if self.field_of_view.is_visible(x, y) or self.god.vision:
			return cell.terrain.sprite
		elif cell.visited and cell.terrain.remembered:
			return cell.terrain.remembered
		return None
	def is_transparent(self, p):
		""" True if cell at position p is transparent/visible to the player. """
		return self.is_transparent_to_monster(p, self.get_player())
	def is_transparent_to_monster(self, p, monster):
		""" True if cell at position p is transparent/visible to a monster. """
		if not self.strata.valid(p):
			return False
		if not self.strata.cell(p.x, p.y).terrain.passable:
			return False
		if self.strata.cell(p.x, p.y).terrain.dark:
			if math.distance(monster.pos, p) >= 1:
				return False
		return True
	def update_vision(self):
		""" Recalculates visibility/FOV for the player.
		May produce Discover events, if some objects come into vision.
		Remembers already seen objects.
		"""
		if not self.get_player():
			return
		current_visible_monsters = []
		current_visible_items = []
		for p in self.field_of_view.update(
				self.get_player().pos,
				is_transparent=self.is_transparent,
				):
			cell = self.strata.cell(p.x, p.y)

			for monster in self.monsters:
				if monster.behavior == monsters.Behavior.PLAYER:
					continue
				if p == monster.pos:
					if monster not in self.visible_monsters:
						self.events.append(messages.DiscoverEvent(monster))
					current_visible_monsters.append(monster)

			for item in self.items:
				if p == item.pos:
					if item not in self.visible_items:
						self.events.append(messages.DiscoverEvent(item))
					current_visible_items.append(item)

			if cell.visited:
				continue
			if p == self.exit_pos:
				self.events.append(messages.DiscoverEvent('>'))
			cell.visited = True
		self.visible_monsters = current_visible_monsters
		self.visible_items = current_visible_items
		if self.field_of_view.is_visible(self.exit_pos.x, self.exit_pos.y):
			self.remembered_exit = True
	def clear_event(self, event=None):
		""" Makes specific event seen, or all of them. """
		if event is None:
			self.events[:] = []
		else:
			self.events.remove(event)
	def build_new_strata(self):
		""" Constructs and populates new random level.
		Transfers player from previous level.
		Updates vision afterwards.
		"""
		builder = self.rng.choice(self.builders)
		Log.debug('Building dungeon: {0}...'.format(builder))
		Log.debug('With RNG: {0}...'.format(self.rng.value))
		builder = builder(self.rng, Size(80, 23))
		builder.build()
		for pos in builder.strata.size:
			builder.strata.set_cell(
					pos.x, pos.y,
					terrain.Cell(self.TERRAIN[builder.strata.cell(pos.x, pos.y)]),
					)

		settler = self.rng.choice(self.settlers)
		Log.debug("Populating dungeon: {0}".format(settler))
		settler = settler(self.rng, builder)
		settler.populate()
		player = self.get_player()
		if player:
			player.pos = builder.start_pos
		else:
			player = monsters.Monster(self.SPECIES['player'], pcg.settlers.Behavior.PLAYER, builder.start_pos)
			player.fill_inventory_from_drops(self.rng, self.ITEMS)
		self.monsters[:] = [player]
		for monster_data in settler.monsters:
			species, monster_data = monster_data[0], monster_data[1:]
			monster_data = (self.SPECIES[species],) + monster_data
			monster = monsters.Monster(*monster_data)
			monster.fill_inventory_from_drops(self.rng, self.ITEMS)
			self.monsters.append(monster)
		self.items[:] = []
		for item_data in settler.items:
			item_type, item_data = item_data[0], item_data[1:]
			item_data = (self.ITEMS[item_type],) + item_data
			self.items.append(items.Item(*item_data))

		Log.debug("Finalizing dungeon...")
		self.exit_pos = builder.exit_pos
		self.strata = builder.strata
		self.remembered_exit = False
		self.update_vision()
		Log.debug("Dungeon is ready.")
	def allow_movement_direction(self, from_point, to_point):
		""" Returns True, if current map allows direct movement from point to point. """
		shift = to_point - from_point
		is_diagonal = abs(shift.x) + abs(shift.y) == 2
		if not is_diagonal:
			return True
		if not self.strata.cell(from_point.x, from_point.y).terrain.allow_diagonal:
			return False
		if not self.strata.cell(to_point.x, to_point.y).terrain.allow_diagonal:
			return False
		return True
	def get_player(self):
		""" Returns player character if exists, or None. """
		return next((monster for monster in self.monsters if monster.behavior == pcg.settlers.Behavior.PLAYER), None)
	def move(self, actor, direction):
		""" Moves monster into given direction (if possible).
		If there is a monster, performs attack().
		May produce all sorts of other events.
		Returns True, is action succeeds, otherwise False.
		"""
		shift = self.SHIFT[direction]
		Log.debug('Shift: {0}'.format(shift))
		new_pos = actor.pos + shift
		if not self.strata.valid(new_pos):
			return False
		if self.god.noclip:
			passable = True
		else:
			passable = self.strata.cell(new_pos.x, new_pos.y).terrain.passable
		if not passable:
			self.events.append(messages.BumpEvent(actor, new_pos))
			return False
		if not self.allow_movement_direction(actor.pos, new_pos):
			self.events.append(messages.BumpEvent(actor, new_pos))
			return False
		monster = self.find_monster(new_pos.x, new_pos.y)
		if monster:
			Log.debug('Monster at dest pos {0}: '.format(new_pos, monster))
			self.attack(actor, monster)
			return True
		Log.debug('Shift is valid, updating pos: {0}'.format(actor.pos))
		self.events.append(messages.MoveEvent(actor, new_pos))
		actor.pos = new_pos
		self.update_vision()
		return True
	def affect_health(self, target, diff):
		""" Changes health of given target.
		Removes monsters from the main list, if health is zero.
		Raises events for health change and death.
		"""
		new_hp = target.hp + diff
		if new_hp < 0:
			new_hp = 0
			diff = new_hp - target.hp
		elif new_hp >= target.species.max_hp:
			new_hp = target.species.max_hp
			diff = new_hp - target.hp
		target.hp += diff
		self.events.append(messages.HealthEvent(target, diff))
		if not target.is_alive():
			self.events.append(messages.DeathEvent(target))
			drops = target.drop_loot()
			for item in drops:
				self.drop_item(target, item)
			self.monsters.remove(target)
	def attack(self, actor, target):
		""" Attacks target monster.
		Raises attack event.
		"""
		self.events.append(messages.AttackEvent(actor, target))
		self.affect_health(target, -1)
		self.update_vision()
	def find_monster(self, x, y):
		""" Return first monster at given cell. """
		for monster in self.monsters:
			if monster.pos.x == x and monster.pos.y == y:
				return monster
		return None
	def find_item(self, x, y):
		""" Return first item at given cell. """
		for item in self.items:
			if item.pos.x == x and item.pos.y == y:
				return item
		return None
	def grab_item_at(self, actor, pos):
		""" Grabs topmost item at given cell and puts to the inventory.
		Produces events.
		"""
		item = self.find_item(pos.x, pos.y)
		if not item:
			return
		self.events.append(messages.GrabItemEvent(actor, item))
		self.items.remove(item)
		actor.inventory.append(item)
	def consume_item(self, monster, item):
		""" Consumes item from inventory (item is removed).
		Applies corresponding effects, if item has any.
		Produces events.
		"""
		assert item in monster.inventory
		monster.inventory.remove(item)
		self.events.append(messages.ConsumeItemEvent(monster, item))
		if item.item_type.effect == items.Effect.HEALING:
			self.affect_health(monster, +5)
	def drop_item(self, monster, item):
		""" Drops item from inventory (item is removed).
		Produces events.
		"""
		assert item in monster.inventory
		item.pos = monster.pos
		monster.inventory.remove(item)
		self.items.append(item)
		self.visible_items.append(item)
		self.events.append(messages.DropItemEvent(monster, item))
	def wield_item(self, monster, item):
		""" Monster equips item from inventory.
		Produces events.
		"""
		assert item in monster.inventory
		if monster.wielding:
			self.unwield_item(monster)
		monster.inventory.remove(item)
		monster.wielding = item
		self.events.append(messages.EquipItemEvent(monster, item))
	def unwield_item(self, monster):
		""" Monster unequips item and puts back to the inventory.
		Produces events.
		"""
		if not monster.wielding:
			return
		item = monster.wielding
		monster.inventory.append(item)
		monster.wielding = None
		self.events.append(messages.UnequipItemEvent(monster, item))
	def jump_to(self, new_pos):
		""" Teleports player to new pos. """
		self.get_player().pos = new_pos
		self.update_vision()
	def descend(self):
		""" Descends onto new level, when standing on exit pos.
		Generates new level.
		Otherwise does nothing.
		"""
		if self.get_player().pos != self.exit_pos:
			return
		self.events.append(messages.DescendEvent(self.get_player()))
		self.build_new_strata()
	def find_path(self, start, find_target):
		""" Find free path from start and until find_target() returns suitable target.
		Otherwise return None.
		"""
		path = math.find_path(
				self.strata, start,
				is_passable=lambda p, from_point: self.strata.cell(p.x, p.y).terrain.passable and self.strata.cell(p.x, p.y).visited and self.allow_movement_direction(from_point, p),
				find_target=find_target,
				)
		if not path:
			return None
		if path[0] == self.get_player().pos: # We're already standing there.
			path.pop(0)
		return path
	def walk_to(self, dest):
		""" Starts auto-walking towards dest, if possible.
		Does not start when monsters are around and produces event.
		"""
		if self.visible_monsters:
			self.events.append(messages.DiscoverEvent('monsters'))
			return
		path = self.find_path(self.get_player().pos,
				find_target=lambda wave: dest if dest in wave else None,
				)
		if path:
			self.movement_queue.extend(path)
	def start_autoexploring(self):
		""" Starts auto-exploring, if there are unknown places.
		Does not start when monsters are around and produces event.
		"""
		if self.visible_monsters:
			self.events.append(messages.DiscoverEvent('monsters'))
			return False
		path = self.find_path(self.get_player().pos,
			find_target=lambda wave: next((target for target in sorted(wave)
			if any(
				not self.strata.cell(p.x, p.y).visited
				for p in self.strata.get_neighbours(target.x, target.y, with_diagonal=True)
				)
			), None),
			)
		if not path:
			return False
		self.movement_queue.extend(path)
		self.autoexploring = True
		return True
	def perform_automovement(self):
		""" Performs next step from auto-movement queue, if any.
		Stops on events.
		"""
		if not self.movement_queue:
			return False
		if self.events:
			Log.debug('New events in FOV, aborting auto-moving mode.')
			return self.stop_automovement()
		Log.debug('Performing queued actions.')
		new_pos = self.movement_queue.pop(0)
		self.jump_to(new_pos)
		if self.movement_queue:
			return True
		if self.autoexploring:
			if not self.start_autoexploring():
				self.autoexploring = False
				raise Game.AutoMovementStopped()
		else:
			raise Game.AutoMovementStopped()
		return True
	def stop_automovement(self):
		""" Stops and resets auto-movement. """
		self.movement_queue[:] = []
		self.autoexploring = False
		raise Game.AutoMovementStopped()

class God:
	""" God mode options.
	- vision: see through everything, ignore FOV/transparency.
	- noclip: walk through everything, ignoring obstacles.
	"""
	def __init__(self):
		self.vision = False
		self.noclip = False
