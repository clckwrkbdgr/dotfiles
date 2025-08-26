import os, sys
import curses, curses.ascii
import json, itertools, copy, functools
import logging
import inspect
from operator import itemgetter
from collections import namedtuple
import six
if six.PY2:
	import itertools
	filter = itertools.ifilter
import vintage
from clckwrkbdgr import xdg
from clckwrkbdgr.utils import get_type_by_name
from clckwrkbdgr.math import Point, Matrix
from clckwrkbdgr.fs import SerializedEntity
import clckwrkbdgr.math
from clckwrkbdgr.collections import dotdict, AutoRegistry
import clckwrkbdgr.collections
import clckwrkbdgr.text
from clckwrkbdgr import tui
import clckwrkbdgr.logging
trace = logging.getLogger('rogue')
from . import game
from .game import Version, Item, Wearable, Player, Room, Tunnel, Scene, GodMode, Dungeon, Event
from . import pcg
from ..engine import events, appliances, ui, Events

class MakeEntity:
	""" Creates builders for bare-properties-based classes to create subclass in one line. """
	def __init__(self, base_classes, *properties):
		""" Properties are either list of strings, or a single strings with space-separated identifiers. """
		self.base_classes = base_classes if clckwrkbdgr.utils.is_collection(base_classes) else (base_classes,)
		self.properties = properties
		if len(self.properties) == 1 and ' ' in self.properties[0]:
			self.properties = self.properties[0].split()
	def __call__(self, class_name, *values):
		""" Creates class object and puts it into global namespace.
		Values should match properties given at init.
		"""
		assert len(self.properties) == len(values), len(values)
		entity_class = type(class_name, self.base_classes, dict(zip(self.properties, values)))
		globals()[class_name] = entity_class
		return entity_class
class EntityClassDistribution:
	def __init__(self, prob):
		self.prob = prob
		self.classes = []
	def __lshift__(self, entity_class):
		self.classes.append(entity_class)
	def __iter__(self):
		return iter(self.classes)
	def get_distribution(self, param):
		if callable(self.prob):
			value = self.prob(param)
		else:
			value = self.prob
		return [(value, entity_class) for entity_class in self.classes]

class StairsUp(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'stairs up'
	_id = 'enter'
	_can_go_up = True

class DungeonGates(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'exit from the dungeon'
	_id = 'enter'
	_can_go_up = True
	_unlocking_item = McGuffin
	def use(self, who):
		if super().use(who):
			raise GameCompleted()

class StairsDown(appliances.LevelPassage):
	_sprite = Sprite('>', None)
	_name = 'stairs down'
	_id = 'exit'
	_can_go_down = True

class McGuffin(Item):
	_sprite = Sprite("*", None)
	_name = "mcguffin"

class HealingPotion(Item, items.Consumable):
	_sprite = Sprite("!", None)
	_name = "potion"
	def consume(self, who):
		who.affect_health(10)
		return [DrinksHealingPotion(Who=who.name.title())]

make_weapon = MakeEntity(Item, '_sprite _name _attack')
make_weapon('Dagger', '(', 'dagger', 1)
make_weapon('Sword', '(', 'sword', 2)
make_weapon('Axe', '(', 'axe', 4)

make_armor = MakeEntity((Item, Wearable), '_sprite _name _protection')
make_armor('Rags', "[", "rags", 1)
make_armor('Leather', "[", "leather", 2)
make_armor('ChainMail', "[", "chain mail", 3)
make_armor('PlateArmor', "[", "plate armor", 4)

class RealMonster(actors.EquippedMonster):
	_hostile_to = [Player]

	def act(self, dungeon):
		if not dungeon.actor_sees_player(self):
			return
		shift = Point(
				clckwrkbdgr.math.sign(dungeon.get_player().pos.x - self.pos.x),
				clckwrkbdgr.math.sign(dungeon.get_player().pos.y - self.pos.y),
				)
		dungeon.move_actor(self, shift)

class Rogue(Player):
	_hostile_to = [RealMonster]
	_sprite = Sprite("@", None)
	_name = "rogue"
	_max_hp = 25
	_attack = 1
	_max_inventory = 26

animal_drops = [
			(70, None),
			(20, HealingPotion),
			(5, Dagger),
			(5, Rags),
			]
monster_drops = [
			(78, None),
			(3, HealingPotion),
			(3, Dagger),
			(3, Sword),
			(3, Axe),
			(3, Rags),
			(3, Leather),
			(3, ChainMail),
			(1, PlateArmor),
		]
thug_drops = [
			(10, None),
			(20, HealingPotion),
			(30, Dagger),
			(10, Sword),
			(30, Leather),
			]
warrior_drops = [
			(40, None),
			(30, HealingPotion),
			(10, Dagger),
			(5, Sword),
			(10, Leather),
			(5, ChainMail),
			]
super_warrior_drops = [
			(80, None),
			(5, HealingPotion),
			(5, Axe),
			(10, Leather),
			]
easy_monsters = EntityClassDistribution(1)
norm_monsters = EntityClassDistribution(lambda depth: max(0, (depth-2)))
hard_monsters = EntityClassDistribution(lambda depth: max(0, (depth-7)//2))
make_monster = MakeEntity((RealMonster), '_sprite _name _max_hp _attack _drops')
easy_monsters << make_monster('Ant', 'a', 'ant', 5, 1, animal_drops)
easy_monsters << make_monster('Bat', 'b', 'bat', 5, 1, animal_drops)
easy_monsters << make_monster('Cockroach', 'c', 'cockroach', 5, 1, animal_drops)
easy_monsters << make_monster('Dog', 'd', 'dog', 7, 1, animal_drops)
norm_monsters << make_monster('Elf', 'e', 'elf', 10, 2, warrior_drops)
easy_monsters << make_monster('Frog', 'f', 'frog', 5, 1, animal_drops)
norm_monsters << make_monster('Goblin', "g", "goblin", 10, 2, warrior_drops*2)
norm_monsters << make_monster('Harpy', 'h', 'harpy', 10, 2, monster_drops)
norm_monsters << make_monster('Imp', 'i', 'imp', 10, 3, monster_drops)
easy_monsters << make_monster('Jelly', 'j', 'jelly', 5, 2, animal_drops)
norm_monsters << make_monster('Kobold', 'k', 'kobold', 10, 2, warrior_drops)
easy_monsters << make_monster('Lizard', 'l', 'lizard', 5, 1, animal_drops)
easy_monsters << make_monster('Mummy', 'm', 'mummy', 10, 2, monster_drops)
norm_monsters << make_monster('Narc', 'n', 'narc', 10, 2, thug_drops)
norm_monsters << make_monster('Orc', 'o', 'orc', 15, 3, warrior_drops*2)
easy_monsters << make_monster('Pigrat', 'p', 'pigrat', 10, 2, animal_drops)
easy_monsters << make_monster('Quokka', 'q', 'quokka', 5, 1, animal_drops)
easy_monsters << make_monster('Rat', "r", "rat", 5, 1, animal_drops)
norm_monsters << make_monster('Skeleton', 's', 'skeleton', 20, 2, monster_drops)
norm_monsters << make_monster('Thug', 't', 'thug', 15, 3, thug_drops*2)
norm_monsters << make_monster('Unicorn', 'u', 'unicorn', 15, 3, monster_drops)
norm_monsters << make_monster('Vampire', 'v', 'vampire', 20, 2, monster_drops)
easy_monsters << make_monster('Worm', 'w', 'worm', 5, 2, animal_drops)
hard_monsters << make_monster('Exterminator', 'x', 'exterminator', 20, 3, super_warrior_drops)
norm_monsters << make_monster('Yak', 'y', 'yak', 10, 2, animal_drops)
easy_monsters << make_monster('Zombie', 'z', 'zombie', 5, 2, thug_drops)
hard_monsters << make_monster('Angel', 'A', 'angel', 30, 5, super_warrior_drops)
norm_monsters << make_monster('Beholder', 'B', 'beholder', 20, 2, warrior_drops)
hard_monsters << make_monster('Cyborg', 'C', 'cyborg', 20, 5, super_warrior_drops*3)
hard_monsters << make_monster('Dragon', 'D', 'dragon', 40, 5, monster_drops*3)
norm_monsters << make_monster('Elemental', 'E', 'elemental', 10, 2, [])
hard_monsters << make_monster('Floater', 'F', 'floater', 40, 1, animal_drops)
hard_monsters << make_monster('Gargoyle', 'G', 'gargoyle', 30, 3, monster_drops)
hard_monsters << make_monster('Hydra', 'H', 'hydra', 30, 2, monster_drops)
norm_monsters << make_monster('Ichthyander', 'I', 'ichthyander', 20, 2, thug_drops)
hard_monsters << make_monster('Juggernaut', 'J', 'juggernaut', 40, 4, monster_drops)
hard_monsters << make_monster('Kraken', 'K', 'kraken', 30, 3, monster_drops)
norm_monsters << make_monster('Lich', 'L', 'lich', 20, 2, monster_drops)
norm_monsters << make_monster('Minotaur', 'M', 'minotaur', 20, 2, warrior_drops*2)
norm_monsters << make_monster('Necromancer', 'N', 'necromancer', 20, 2, warrior_drops)
hard_monsters << make_monster('Ogre', 'O', 'ogre', 30, 5, super_warrior_drops)
hard_monsters << make_monster('Phoenix', 'P', 'phoenix', 20, 3, monster_drops)
norm_monsters << make_monster('QueenBee', 'Q', 'queen bee', 20, 2, animal_drops)
hard_monsters << make_monster('Revenant', 'R', 'revenant', 20, 3, super_warrior_drops)
norm_monsters << make_monster('Snake', 'S', 'snake', 10, 2, animal_drops)
hard_monsters << make_monster('Troll', "T", "troll", 25, 5, super_warrior_drops)
norm_monsters << make_monster('Unseen', 'U', 'unseen', 10, 2, thug_drops)
norm_monsters << make_monster('Viper', 'V', 'viper', 10, 2, animal_drops)
hard_monsters << make_monster('Wizard', 'W', 'wizard', 40, 5, thug_drops*2)
hard_monsters << make_monster('Xenomorph', 'X', 'xenomorph', 30, 3, animal_drops)
norm_monsters << make_monster('Yeti', 'Y', 'yeti', 10, 2, animal_drops)
norm_monsters << make_monster('Zealot', 'Z', 'zealot', 10, 2, thug_drops)

class GodModeSwitched(events.Event): FIELDS = 'name state'
events.Event.on(GodModeSwitched)(lambda event:"God {name} -> {state}".format(name=event.name, state=event.state))

events.Event.on(Event.NeedKey)(lambda event:"You cannot escape the dungeon without {0}!".format(event.key))
events.Event.on(Event.GoingUp)(lambda event:"Going up...")
events.Event.on(Event.GoingDown)(lambda event:"Going down...")
class CannotGoBelow(events.Event): FIELDS = ''
events.Event.on(CannotGoBelow)(lambda event:"No place down below.")
events.Event.on(Event.CannotDig)(lambda event:"Cannot dig through the ground.")
events.Event.on(Event.CannotReachCeiling)(lambda event:"Cannot reach the ceiling.")

class NoSuchItem(events.Event): FIELDS = 'char'
events.Event.on(NoSuchItem)(lambda event:"No such item '{char}'.".format(char=event.char))
events.Event.on(Events.InventoryIsFull)(lambda event: "Inventory is full! Cannot pick up {item}".format(item=event.item.name))
events.Event.on(Events.GrabItem)(lambda event: "Grabbed {item}.".format(who=event.who.name, item=event.item.name))
events.Event.on(Events.NothingToPickUp)(lambda event:"There is nothing here to pick up.")
class InventoryEmpty(events.Event): FIELDS = ''
events.Event.on(InventoryEmpty)(lambda event:"Inventory is empty.")
events.Event.on(Events.DropItem)(lambda event:"Dropped {item}.".format(Who=event.who.name.title(), item=event.item.name))
class DropsItem(events.Event): FIELDS = 'Who'
events.Event.on(DropsItem)(lambda event:"{Who} drops {item}.".format(Who=event.Who))

events.Event.on(Events.NotConsumable)(lambda event:"Cannot consume {item}.".format(item=event.item.name))
events.Event.on(Events.ConsumeItem)(lambda event:"Consumed {item}.".format(item=event.item.name))
class DrinksHealingPotion(events.Event): FIELDS = 'Who'
events.Event.on(DrinksHealingPotion)(lambda event:"{Who} heals itself.".format(Who=event.Who))

class NothingToUnwield(events.Event): FIELDS = ''
events.Event.on(NothingToUnwield)(lambda event:"Nothing is wielded already.")
events.Event.on(Unwielding)(lambda event:"Unwielding {item}.".format(item=event.item.name))
events.Event.on(Wielding)(lambda event:"Wielding {item}.".format(item=event.item.name))

events.Event.on(Event.NotWearable)(lambda event:"Cannot wear {item}.".format(item=event.item.name))
class NothingToTakeOff(events.Event): FIELDS = ''
events.Event.on(NothingToTakeOff)(lambda event:"Nothing is worn already.")
events.Event.on(TakingOff)(lambda event:"Taking off {item}.".format(item=event.item.name))
events.Event.on(Wearing)(lambda event:"Wearing {item}.".format(item=event.item.name))

events.Event.on(Events.Attack)(lambda event: "{Who} hit {whom} for {damage} hp.".format(Who=event.who.name.title(), whom=event.whom.name, damage=event.damage))
events.Event.on(Events.Death)(lambda event:"{Who} is dead.".format(Who=event.who.name.title()))
@events.Event.on(Events.BumpIntoTerrain)
def bumps_into_terrain(event):
	if event.who != dungeon.get_player():
		return "{Who} bumps into wall.".format(Who=event.who.name.title())
events.Event.on(Event.BumpIntoMonster)(lambda event:"{Who} bumps into {whom}.".format(Who=event.who.name.title(), whom=event.whom.name))

class WelcomeBack(Event): FIELDS = 'who'
events.Event.on(WelcomeBack)(lambda event:"Welcome back, {who}!".format(who=event.who.name))

class _Builder(builders.Builder):
	class _Dungeon(clckwrkbdgr.pcg.rogue.Dungeon):
		ROOM_CLASS = Room
		TUNNEL_CLASS = Tunnel
		MAX_TUNNEL_ETCHING_TRIES = 5
	def __init__(self, depth, *args, **kwargs):
		self.depth = depth
		super().__init__(*args, **kwargs)
	def fill_grid(self, grid):
		self.dungeon = self._Dungeon(self.size, (3, 3))
	def generate_appliances(self):
		self.enter_room_key = self.rng.choice(list(result.rooms.keys()))
		enter_room = result.rooms.cell(self.enter_room_key)
		yield (self.pos_in_rect(enter_room), 'enter')

		if not is_bottom:
			exit_room_key = self.rng.choice(list(set(result.rooms.keys()) - {self.enter_room_key}))
			exit_room = result.rooms.cell(exit_room_key)
			yield (self.pos_in_rect(exit_room), 'exit')
	def generate_items(self):
		item_distribution = [
			(50, HealingPotion),
			(self.depth, Dagger),
			(self.depth // 2, Sword),
			(max(0, (self.depth-5) // 3), Axe),
			(self.depth, Rags),
			(self.depth // 2, Leather),
			(max(0, (self.depth-5) // 3), ChainMail),
			(max(0, (self.depth-10) // 3), PlateArmor),
			]
		for _ in self.distribute(WeightedDistribution, item_distribution, self.amont_fixed(2, 4)
			):
			if _ is None:
				continue
			room = self.rng.choice(list(result.rooms.values()))
			pos = self.pos_in_rect(room)
			yield pos, _()
		if is_bottom:
			exit_room_key = self.rng.choice(list(set(result.rooms.keys()) - {self.enter_room_key}))
			exit_room = result.rooms.cell(exit_room_key)
			yield (self.pos_in_rect(exit_room), 'exit_item')
	def generate_actors(self):
		monster_distribution = list(itertools.chain(
			easy_monsters.get_distribution(self.depth),
			norm_monsters.get_distribution(self.depth),
			hard_monsters.get_distribution(self.depth),
			))
		available_rooms = [room for room in result.rooms.values() if room != enter_room and room != exit_room]
		for pos, monster in self.distribute(WeightedDistribution, monster_distribution,  self.amont_fixed(5)):
			if monster is None:
				continue
			room = self.rng.choice(list(result.rooms.values()))
			pos = self.pos_in_rect(room)
			monster = monster()
			monster.pos = pos
			monster.fill_drops(self.rng)
			yield monster

class RogueDungeonGenerator(pcg.Generator):
	MAX_LEVELS = 26
	SIZE = Size(78, 21)
	def build_level(self, scene, level_id):
		if level_id < 0 or level_id >= self.MAX_LEVELS:
			raise KeyError("Invalid level ID: {0} (supports only [0; {1}))".format(level_id, self.MAX_LEVELS))
		depth = level_id
		is_bottom = depth >= (self.MAX_LEVELS - 1)

		enter_object_type = StairsUp if level_id > 0 else DungeonGates
		prev_level_id = level_id - 1 if level_id > 0 else None
		next_level_id = level_id + 1 if not is_bottom else None
		builder = _Builder(depth, random, self.SIZE)
		builder.map_key(enter=enter_object_type(prev_level_id, 'exit'))
		if is_bottom:
			builder.map_key(exit_item=McGuffin())
		else:
			builder.map_key(exit=StairsDown(next_level_id, 'enter'))
		builder.generate()
		scene.size = self.SIZE
		scene.rooms = builder.dungeon.grid
		scene.tunnels = builder.dungeon.tunnels
		scene.objects = list(builder.make_appliances())
		scene.items = list(builder.make_items())
		scene.monsters = list(builder.make_actors())

class ExitWithoutSave(tui.app.AppExit):
	def __init__(self):
		super(ExitWithoutSave, self).__init__(False)

class GameCompleted(Exception):
	pass

def to_main_screen(mode):
	return MessageView(StatusLine(MainGame, mode.data), mode.data)

class MessageView(tui.widgets.MessageLineOverlay):
	def get_new_messages(self):
		for message in self.data.process_events():
			trace.debug("Message posted: {0}".format(message))
			yield message
	def force_ellipsis(self):
		return not self.data.get_player().is_alive()

StatusSection = tui.widgets.StatusLine.LabeledSection
class StatusLine(tui.widgets.StatusLine):
	CORNER = "[?]"
	INDICATORS = [
			ui.Indicator('Depth', 2, lambda dungeon: 1+dungeon.current_level_id),
			ui.Indicator("HP", 6, lambda dungeon: "{0}/{1}".format(dungeon.get_player().hp, dungeon.get_player().max_hp)),
			ui.Indicator("Items", 2, lambda dungeon:(
				None if not dungeon.get_player().inventory else (
					''.join(item.sprite for item in dungeon.get_player().inventory)
					if len(dungeon.get_player().inventory) <= 2
					else len(dungeon.get_player().inventory)
					))),
			ui.Indicator("Wld", 7, lambda dungeon: dungeon.get_player().wielding.name if dungeon.get_player().wielding else None),
			ui.Indicator("Wear", 7, lambda dungeon: dungeon.get_player().wearing.name if dungeon.get_player().wearing else None),
			ui.Indicator("Here", 1, lambda dungeon: getattr(next(dungeon.scene.iter_items_at(dungeon.get_player().pos), next(dungeon.scene.iter_appliances_at(dungeon.get_player().pos), None)), 'sprite', None)),
			]

Controls = AutoRegistry()

class MainGame(ui.MainGame):
	_full_redraw = True
	def get_viewrect(self):
		return None
	def get_map_shift(self):
		return Point(0, 1)
	def _view(self, window):
		self.draw_map(ui)
	def _control(self, ch):
		try:
			new_mode = Controls[str(ch)](self)
			if new_mode:
				return new_mode
			self.game.process_others()
			if not dungeon.get_player().is_alive():
				return MessageView(Grave, self.data)
		except KeyError:
			trace.debug("Unknown key: {0}".format(ch))
			pass

	@Controls('Q')
	def quit(self):
		""" Abandon game. """
		return SuicideAttempt(to_main_screen(self), self.data)
	@Controls('~')
	def god_mode(self):
		return GodModeAction
	@Controls('?')
	def show_help(self):
		""" Show help message. """
		return HelpScreen
	@Controls('>')
	def descend(self):
		""" Go down. """
		dungeon = self.data
		if dungeon.descend(dungeon.get_player()):
			return to_main_screen(self)
	@Controls('<')
	def ascend(self):
		""" Go up. """
		dungeon = self.data
		try:
			if dungeon.ascend(dungeon.get_player()):
				return to_main_screen(self)
		except GameCompleted:
			return Greetings
	@Controls('g')
	def grab(self):
		""" Grab item. """
		dungeon = self.data
		dungeon.grab_item_here(dungeon.get_player())
	@Controls('d')
	def drop(self):
		""" Drop item. """
		dungeon = self.data
		if not dungeon.get_player().inventory:
			dungeon.fire_event(InventoryEmpty())
		else:
			return QuickDropItem(to_main_screen(self), self.data)
	@Controls('e')
	def eat(self):
		""" Consume item. """
		dungeon = self.data
		if not dungeon.get_player().inventory:
			dungeon.fire_event(InventoryEmpty())
		else:
			return QuickConsumeItem(to_main_screen(self), self.data)
	@Controls('w')
	def wield(self):
		""" Wield item. """
		dungeon = self.data
		if not dungeon.get_player().inventory:
			dungeon.fire_event(InventoryEmpty())
		else:
			return QuickWieldItem(to_main_screen(self), self.data)
	@Controls('U')
	def unwield(self):
		""" Unwield item. """
		dungeon = self.data
		if not dungeon.get_player().wielding:
			dungeon.fire_event(NothingToUnwield())
		else:
			item = dungeon.get_player().unwield()
			self.data.fire_event(Event.Unwielding(self, item))
	@Controls('W')
	def wear(self):
		""" Wear item. """
		dungeon = self.data
		if not dungeon.get_player().inventory:
			dungeon.fire_event(InventoryEmpty())
		else:
			return QuickWearItem(to_main_screen(self), self.data)
	@Controls('T')
	def take_off(self):
		""" Take item off. """
		dungeon = self.data
		if not dungeon.get_player().wearing:
			dungeon.fire_event(NothingToTakeOff())
		else:
			item = dungeon.get_player().take_off()
			self.data.fire_event(Event.TakingOff(self, item))
	@Controls('i')
	def inventory(self):
		""" Toggle inventory. """
		return Inventory

class GodModeAction(tui.widgets.Menu):
	KEYS_TO_CLOSE = [curses.ascii.ESC, ord('~')]
	def items(self):
		return [
				tui.widgets.Menu.Item('v', 'see all: {0}'.format('ON' if self.data.god.vision else 'off'), 'vision'),
				]
	def on_close(self):
		return to_main_screen(self)
	def on_item(self, item):
		new_state = not getattr(self.data.god, item.data)
		setattr(self.data.god, item.data, new_state)
		self.data.fire_event(GodModeSwitched(name=item.text, state='ON' if new_state else 'off'))
		return to_main_screen(self)

class ConsumeItem:
	def prompt(self): return "Which item to consume?"
	def item_action(self, index):
		item = self.data.get_player().inventory[index]
		self.data.consume_item(self.data.get_player(), item)

class DropItem:
	def prompt(self): return "Which item to drop?"
	def item_action(self, index):
		item = self.data.get_player().inventory[index]
		self.data.drop_item(self.data.get_player(), item)

class WieldItem:
	def prompt(self): return "Which item to wield?"
	def item_action(self, index):
		item = self.data.get_player().inventory[index]
		self.data.wield_item(self.data.get_player(), item)

class WearItem:
	def prompt(self): return "Which item to wear?"
	def item_action(self, index):
		item = self.data.get_player().inventory[index]
		self.data.wear_item(self.data.get_player(), item)

class QuickItemSelection(tui.widgets.Prompt):
	def extended_mode(self):
		raise NotImplementedError
	def choices(self):
		return [chr(ord('a') + i) for i in range(len(self.data.get_player().inventory))] + ['*']
	def on_choice(self, key):
		if key == '*':
			return self.extended_mode()
		index = key.value - ord('a')
		self.item_action(index)
		return self.actual_mode

class QuickConsumeItem(ConsumeItem, QuickItemSelection):
	def extended_mode(self):
		return ConsumeFromInventory

class QuickDropItem(DropItem, QuickItemSelection):
	def extended_mode(self):
		return DropFromInventory

class QuickWearItem(WearItem, QuickItemSelection):
	def extended_mode(self):
		return WearFromInventory

class QuickWieldItem(WieldItem, QuickItemSelection):
	def extended_mode(self):
		return WieldFromInventory

class Inventory(tui.widgets.Menu):
	COLUMNS = 2
	KEYS_TO_CLOSE = ['i', curses.ascii.ESC]
	def on_close(self):
		return to_main_screen(self)
	def prompt(self):
		if not self.data.get_player().inventory:
			return "(empty)"
		return ""
	def items(self):
		for index, item in enumerate(self.data.get_player().inventory):
			line = "{0} {1}".format(item.sprite, item.name)
			if self.data.get_player().wielding == item:
				line += " (wielding)"
			if self.data.get_player().wearing == item:
				line += " (wearing)"
			key = ord('a') + index
			yield tui.widgets.Menu.Item(key, line, key)
	def on_item(self, item):
		if hasattr(self, 'item_action'):
			self.item_action(item.data - ord('a'))
			return to_main_screen(self)
		return None

class ConsumeFromInventory(ConsumeItem, Inventory):
	pass

class DropFromInventory(DropItem, Inventory):
	pass

class WieldFromInventory(WieldItem, Inventory):
	pass

class WearFromInventory(WearItem, Inventory):
	pass

class HelpScreen(tui.widgets.TextScreen):
	_full_redraw = True
	LINES = ["{0} - {1}".format(''.join(map(itemgetter(1), keys)), text)
			for text, keys in itertools.groupby(sorted([
				(inspect.getdoc(value), key)
				for key, value
				in Controls.items()
				if value.__doc__
				]), key=itemgetter(0))]
	def on_close(self):
		return to_main_screen(self)

class SuicideAttempt(tui.widgets.Confirmation):
	MESSAGE = "Do you really want to quit without saving?"
	def on_yes(self):
		raise ExitWithoutSave()

class Grave(tui.widgets.TextScreen):
	LINES = [
			"You failed to reach mcguffin!"
			]
	RETURN_VALUE = ExitWithoutSave

class Greetings(tui.widgets.TextScreen):
	LINES = [
			"Mcguffin is successfully retrieved!"
			]
	RETURN_VALUE = ExitWithoutSave

class Game(tui.app.App):
	pass

class RogueDungeon(Dungeon):
	def make_scene(self, scene_id):
		return Scene(RogueDungeonGenerator())
	def make_player(self):
		rogue = super(RogueDungeon, self).make_player()
		rogue.grab(Dagger())
		return rogue

def main(stdscr):
	curses.curs_set(0)

	with SerializedEntity(xdg.save_data_path('dotrogue')/'rogue.sav', Version._top(), entity_name='dungeon', unlink=True, readable=True) as savefile:
		dungeon = Dungeon()
		if savefile.entity:
			dungeon.load(savefile.entity)
		else:
			dungeon.generate(0)
			savefile.reset(dungeon)

		game = Game(stdscr)
		return_code = game.run(to_main_screen(dotdict(data=dungeon)))
		if dungeon.is_finished():
			savefile.reset()
		else:
			game.save(savefile.entity)

import click
@click.command()
@click.option('--debug', is_flag=True)
def cli(debug=False):
	clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	curses.wrapper(main)

if __name__ == '__main__':
	cli()
