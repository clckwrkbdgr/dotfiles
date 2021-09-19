import os, sys
import curses, curses.ascii
import json, itertools, copy, functools
import logging
import inspect
from operator import itemgetter
from collections import namedtuple
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
from clckwrkbdgr.events import Events, MessageEvent
from clckwrkbdgr.rogue import game
from clckwrkbdgr.rogue.game import Version, Item, Consumable, Wearable, Monster, Room, Tunnel, GridRoomMap, GridRoomMap as Map, Furniture, LevelPassage, GodMode, Dungeon, Event
from clckwrkbdgr.rogue import pcg

class StairsUp(LevelPassage):
	_sprite = '<'
	_name = 'stairs up'
	_id = 'enter'
	_can_go_up = True

class DungeonGates(LevelPassage):
	_sprite = '<'
	_name = 'exit from the dungeon'
	_id = 'enter'
	_can_go_up = True
	def use(self, who):
		if who.has_item(McGuffin):
			raise GameCompleted()
		raise Furniture.Locked(McGuffin)

class StairsDown(LevelPassage):
	_sprite = '>'
	_name = 'stairs down'
	_id = 'exit'
	_can_go_down = True

class McGuffin(Item):
	_sprite = "*"
	_name = "mcguffin"

class HealingPotion(Item, Consumable):
	_sprite = "!"
	_name = "potion"
	def consume_by(self, who):
		who.heal(10)
		Events().trigger(DrinksHealingPotion(Who=who.name.title()))
		return True

class Dagger(Item):
	_sprite = "("
	_name = "dagger"
	_attack = 1

class Sword(Item):
	_sprite = "("
	_name = "sword"
	_attack = 2

class Axe(Item):
	_sprite = "("
	_name = "axe"
	_attack = 4

class Rags(Item, Wearable):
	_sprite = "["
	_name = "rags"
	_protection = 1

class Leather(Item, Wearable):
	_sprite = "["
	_name = "leather"
	_protection = 2

class ChainMail(Item, Wearable):
	_sprite = "["
	_name = "chain mail"
	_protection = 3

class PlateArmor(Item, Wearable):
	_sprite = "["
	_name = "plate armor"
	_protection = 4

class Rogue(Monster):
	_hostile_to = [Monster]
	_sprite = "@"
	_name = "rogue"
	_max_hp = 25
	_attack = 1
	_max_inventory = 26

class RealMonster(Monster):
	_hostile_to = [Rogue]

class Rat(RealMonster):
	_sprite = "r"
	_name = "rat"
	_max_hp = 5
	_attack = 1
	_drops = [
			(70, None),
			(20, HealingPotion),
			(5, Dagger),
			(5, Rags),
			]

class Goblin(RealMonster):
	_sprite = "g"
	_name = "goblin"
	_max_hp = 10
	_attack = 2
	_drops = 2*[
			(40, None),
			(30, HealingPotion),
			(10, Dagger),
			(5, Sword),
			(10, Leather),
			(5, ChainMail),
			]

class Troll(RealMonster):
	_sprite = "T"
	_name = "troll"
	_max_hp = 25
	_attack = 5
	_drops = [
			(80, None),
			(5, HealingPotion),
			(5, Axe),
			(10, Leather),
			]

class GodModeSwitched(MessageEvent): _message = "God {name} -> {state}"

class NeedMcGuffin(MessageEvent): _message = "You cannot escape the dungeon without mcguffin!"
class GoingUp(MessageEvent): _message = "Going up..."
class GoingDown(MessageEvent): _message = "Going down..."
class CannotGoBelow(MessageEvent): _message = "No place down below."
class CannotDig(MessageEvent): _message = "Cannot dig through the ground."
class CannotReachCeiling(MessageEvent): _message = "Cannot reach the ceiling."

class NoSuchItem(MessageEvent): _message = "No such item '{char}'."
class InventoryFull(MessageEvent): _message = "Inventory is full! Cannot pick up {item}"
class GrabbedItem(MessageEvent): _message = "Grabbed {item}."
class NothingToPickUp(MessageEvent): _message = "There is nothing here to pick up."
class InventoryEmpty(MessageEvent): _message = "Inventory is empty."
class ItemDropped(MessageEvent): _message = "Dropped {item}."
class DropsItem(MessageEvent): _message = "{Who} drops {item}."

class CannotConsume(MessageEvent): _message = "Cannot consume {item}."
class ItemConsumed(MessageEvent): _message = "Consumed {item}."
class DrinksHealingPotion(MessageEvent): _message = "{Who} heals itself."

class NothingToUnwield(MessageEvent): _message = "Nothing is wielded already."
class Unwielding(MessageEvent): _message = "Unwielding {item}."
class Wielding(MessageEvent): _message = "Wielding {item}."

class CannotWear(MessageEvent): _message = "Cannot wear {item}."
class NothingToTakeOff(MessageEvent): _message = "Nothing is worn already."
class TakingOff(MessageEvent): _message = "Taking off {item}."
class Wearing(MessageEvent): _message = "Wearing {item}."

class Attacking(MessageEvent): _message = "{Who} hit {whom} for {damage} hp."
class IsDead(MessageEvent): _message = "{Who} is dead."
class BumpsIntoWall(MessageEvent): _message = "{Who} bumps into wall."
class BumpsIntoOther(MessageEvent): _message = "{Who} bumps into {whom}."
class WelcomeBack(MessageEvent): _message = "Welcome back, {who}!"
Event.register('WelcomeBack', 'who')

class RogueDungeonGenerator(pcg.Generator):
	MAX_LEVELS = 26
	def build_level(self, level_id):
		if level_id < 0 or level_id >= self.MAX_LEVELS:
			raise KeyError("Invalid level ID: {0} (supports only [0; {1}))".format(level_id, self.MAX_LEVELS))
		depth = level_id
		is_bottom = depth >= self.MAX_LEVELS
		result = self.original_rogue_dungeon(
				map_size=(78, 21),
				grid_size=(3, 3),
				room_class=Room, tunnel_class=Tunnel,
				item_distribution = [
					(50, HealingPotion),
					(depth, Dagger),
					(depth // 2, Sword),
					(max(0, (depth-5) // 3), Axe),
					(depth, Rags),
					(depth // 2, Leather),
					(max(0, (depth-5) // 3), ChainMail),
					(max(0, (depth-10) // 3), PlateArmor),
					],
				item_amount=(2, 4),
				monster_distribution = [
					(10, Rat),
					(depth, Goblin),
					(max(0, (depth-5) // 2), Troll),
					],
				monster_amount=5,
				prev_level_id=level_id - 1 if level_id > 0 else None,
				next_level_id=level_id + 1 if not is_bottom else None,
				enter_object_type=StairsUp if level_id > 0 else DungeonGates,
				exit_object_type=StairsDown,
				enter_connected_id='exit',
				exit_connected_id='enter',
				item_instead_of_exit=McGuffin if is_bottom else None,
				)
		result.level_id = level_id
		return GridRoomMap(**vars(result))

class ExitWithoutSave(tui.app.AppExit):
	def __init__(self):
		super(ExitWithoutSave, self).__init__(False)

class SaveAndExit(tui.app.AppExit):
	def __init__(self):
		super(SaveAndExit, self).__init__(True)

class GameCompleted(Exception):
	pass

def to_main_screen(mode):
	return MessageView(StatusLine(MainGame, mode.data), mode.data)

class MessageView(tui.widgets.MessageLineOverlay):
	def get_new_messages(self):
		process_game_events(self.data, self.data.history)
		self.data.history.clear()

		events = Events()
		while events.listen():
			trace.debug("Message posted: {0}: {1}".format(repr(events.current), str(events.current)))
			yield events.current
	def force_ellipsis(self):
		return not self.data.rogue.is_alive()

StatusSection = tui.widgets.StatusLine.LabeledSection
class StatusLine(tui.widgets.StatusLine):
	CORNER = "[?]"
	SECTIONS = [
			StatusSection('Lvl', 2, lambda dungeon: 1+dungeon.current_level_id),
			StatusSection("HP", 6, lambda dungeon: "{0}/{1}".format(dungeon.rogue.hp, dungeon.rogue.max_hp)),
			StatusSection("Items", 2, lambda dungeon:(
				None if not dungeon.rogue.inventory else (
					''.join(item.sprite for item in dungeon.rogue.inventory)
					if len(dungeon.rogue.inventory) <= 2
					else len(dungeon.rogue.inventory)
					))),
			StatusSection("Wld", 7, lambda dungeon: dungeon.rogue.wielding.name if dungeon.rogue.wielding else None),
			StatusSection("Wear", 7, lambda dungeon: dungeon.rogue.wearing.name if dungeon.rogue.wearing else None),
			StatusSection("Here", 1, lambda dungeon: getattr(next(dungeon.current_level.items_at(dungeon.rogue.pos), next(dungeon.current_level.objects_at(dungeon.rogue.pos), None)), 'sprite', None)),
			]

Controls = AutoRegistry()

class MainGame(tui.app.MVC):
	_full_redraw = True
	def _view(self, window):
		stdscr, dungeon = window, self.data

		trace.debug(list(dungeon.current_level.rooms.keys()))
		for room in dungeon.current_level.rooms.values():
			if not dungeon.is_remembered(room):
				continue
			stdscr.addstr(1 + room.top, room.left, "+")
			stdscr.addstr(1 + room.bottom, room.left, "+")
			stdscr.addstr(1 + room.top, room.right, "+")
			stdscr.addstr(1 + room.bottom, room.right, "+")
			for x in range(room.left+1, room.right):
				stdscr.addstr(1 + room.top, x, "-")
				stdscr.addstr(1 + room.bottom, x, "-")
			for y in range(room.top+1, room.bottom):
				stdscr.addstr(1 + y, room.left, "|")
				stdscr.addstr(1 + y, room.right, "|")
			if dungeon.is_visible(room):
				for y in range(room.top+1, room.bottom):
					for x in range(room.left+1, room.right):
						stdscr.addstr(1 + y, x, ".")
			else:
				for y in range(room.top+1, room.bottom):
					for x in range(room.left+1, room.right):
						stdscr.addstr(1 + y, x, " ")
		for tunnel in dungeon.current_level.tunnels:
			for cell in tunnel.iter_points():
				if dungeon.is_visible(tunnel, cell):
					stdscr.addstr(1 + cell.y, cell.x, "#")
			if dungeon.is_visible(tunnel, tunnel.start):
				stdscr.addstr(1 + tunnel.start.y, tunnel.start.x, "+")
			if dungeon.is_visible(tunnel, tunnel.stop):
				stdscr.addstr(1 + tunnel.stop.y, tunnel.stop.x, "+")

		for pos, obj in dungeon.current_level.objects:
			if dungeon.is_remembered(pos) or dungeon.is_visible(pos):
				stdscr.addstr(1 + pos.y, pos.x, obj.sprite)
		for pos, item in dungeon.current_level.items:
			if dungeon.is_remembered(pos) or dungeon.is_visible(pos):
				stdscr.addstr(1 + pos.y, pos.x, item.sprite)

		for monster in dungeon.current_level.monsters:
			if dungeon.is_visible(monster.pos):
				stdscr.addstr(1 + monster.pos.y, monster.pos.x, monster.sprite)
		stdscr.addstr(1 + dungeon.rogue.pos.y, dungeon.rogue.pos.x, dungeon.rogue.sprite)

	def _control(self, ch):

		self.step_is_over = False
		try:
			new_mode = Controls[str(ch)](self)
			if new_mode:
				return new_mode
			if not self.step_is_over:
				return
			return self.process_others()
		except KeyError:
			trace.debug("Unknown key: {0}".format(ch))
			pass

	@Controls('Q')
	def quit(self):
		""" Abandon game. """
		return SuicideAttempt(to_main_screen(self), self.data)
	@Controls('S')
	def save_and_exit(self):
		""" Save & exit. """
		raise SaveAndExit()
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
		stairs_here = next(filter(lambda obj: isinstance(obj, LevelPassage) and obj.can_go_down, dungeon.current_level.objects_at(dungeon.rogue.pos)), None)
		if stairs_here:
			dungeon.use_stairs(stairs_here)
			Events().trigger(GoingDown())
			return to_main_screen(self)
		else:
			Events().trigger(CannotDig())
	@Controls('<')
	def ascend(self):
		""" Go up. """
		dungeon = self.data
		stairs_here = next(filter(lambda obj: isinstance(obj, LevelPassage) and obj.can_go_up, dungeon.current_level.objects_at(dungeon.rogue.pos)), None)
		if stairs_here:
			try:
				dungeon.use_stairs(stairs_here)
				Events().trigger(GoingUp())
				return to_main_screen(self)
			except Furniture.Locked:
				Events().trigger(NeedMcGuffin())
			except GameCompleted:
				return Greetings
		else:
			Events().trigger(CannotReachCeiling())
	@Controls('g')
	def grab(self):
		""" Grab item. """
		dungeon = self.data
		item_here = next( (index for index, (pos, item) in enumerate(reversed(dungeon.current_level.items)) if pos == dungeon.rogue.pos), None)
		trace.debug("Items: {0}".format(dungeon.current_level.items))
		trace.debug("Rogue: {0}".format(dungeon.rogue.pos))
		trace.debug("Items here: {0}".format([(index, pos, item) for index, (pos, item) in enumerate(reversed(dungeon.current_level.items)) if pos == dungeon.rogue.pos]))
		trace.debug("Item here: {0}".format(item_here))
		if item_here is not None:
			item_here = len(dungeon.current_level.items) - 1 - item_here # Index is from reversed list.
			trace.debug("Unreversed item here: {0}".format(item_here))
			_, item = dungeon.current_level.items[item_here]
			self.data.history += dungeon.current_level.grab_item(dungeon.rogue, item)
			self.step_is_over = True
		else:
			Events().trigger(NothingToPickUp())
	@Controls('d')
	def drop(self):
		""" Drop item. """
		dungeon = self.data
		if not dungeon.rogue.inventory:
			Events().trigger(InventoryEmpty())
		else:
			return QuickDropItem(to_main_screen(self), self.data)
	@Controls('e')
	def eat(self):
		""" Consume item. """
		dungeon = self.data
		if not dungeon.rogue.inventory:
			Events().trigger(InventoryEmpty())
		else:
			return QuickConsumeItem(to_main_screen(self), self.data)
	@Controls('w')
	def wield(self):
		""" Wield item. """
		dungeon = self.data
		if not dungeon.rogue.inventory:
			Events().trigger(InventoryEmpty())
		else:
			return QuickWieldItem(to_main_screen(self), self.data)
	@Controls('U')
	def unwield(self):
		""" Unwield item. """
		dungeon = self.data
		if not dungeon.rogue.wielding:
			Events().trigger(NothingToUnwield())
		else:
			self.data.history += dungeon.rogue.wield(None)
	@Controls('W')
	def wear(self):
		""" Wear item. """
		dungeon = self.data
		if not dungeon.rogue.inventory:
			Events().trigger(InventoryEmpty())
		else:
			return QuickWearItem(to_main_screen(self), self.data)
	@Controls('T')
	def take_off(self):
		""" Take item off. """
		dungeon = self.data
		if not dungeon.rogue.wearing:
			Events().trigger(NothingToTakeOff())
		else:
			self.data.history += dungeon.rogue.wear(None)
	@Controls('i')
	def inventory(self):
		""" Toggle inventory. """
		return Inventory
	@Controls('.')
	def wait(self):
		""" Wait. """
		self.step_is_over = True
	@Controls('h')
	def move_west(self):
		""" Move around. """
		self.move_by(Point(-1,  0))
	@Controls('j')
	def move_south(self):
		""" Move around. """
		self.move_by(Point( 0, +1))
	@Controls('k')
	def move_north(self):
		""" Move around. """
		self.move_by(Point( 0, -1))
	@Controls('l')
	def move_east(self):
		""" Move around. """
		self.move_by(Point(+1,  0))
	@Controls('y')
	def move_north_west(self):
		""" Move around. """
		self.move_by(Point(-1, -1))
	@Controls('u')
	def move_north_east(self):
		""" Move around. """
		self.move_by(Point(+1, -1))
	@Controls('b')
	def move_south_west(self):
		""" Move around. """
		self.move_by(Point(-1, +1))
	@Controls('n')
	def move_south_east(self):
		""" Move around. """
		self.move_by(Point(+1, +1))

	def move_by(self, shift):
		dungeon = self.data
		self.data.history += dungeon.move_monster(dungeon.rogue, dungeon.rogue.pos + shift)
		dungeon.current_level.visit(dungeon.rogue.pos)
		self.step_is_over = True

	def process_others(self):
		dungeon = self.data
		for monster in dungeon.current_level.monsters:
			if not dungeon.current_room:
				continue
			sees_rogue = dungeon.current_room.contains(monster.pos)
			if not sees_rogue:
				continue
			shift = Point(
					clckwrkbdgr.math.sign(dungeon.rogue.pos.x - monster.pos.x),
					clckwrkbdgr.math.sign(dungeon.rogue.pos.y - monster.pos.y),
					)
			new_pos = monster.pos + shift
			self.data.history += dungeon.move_monster(monster, new_pos, with_tunnels=False)

		if not dungeon.rogue.is_alive():
			return MessageView(Grave, self.data)

def process_game_events(dungeon, events):
	for event in events:
		if isinstance(event, Event.BumpIntoTerrain):
			if event.who != dungeon.rogue:
				Events().trigger(BumpsIntoWall(Who=event.who.name.title()))
		elif isinstance(event, Event.BumpIntoMonster):
			Events().trigger(BumpsIntoOther(Who=event.who.name.title(), whom=event.whom.name))
		elif isinstance(event, Event.AttackMonster):
			Events().trigger(Attacking(Who=event.who.name.title(), whom=event.whom.name, damage=event.damage))
		elif isinstance(event, Event.MonsterDied):
			Events().trigger(IsDead(Who=event.who.name.title()))
		elif isinstance(event, Event.MonsterDroppedItem):
			Events().trigger(DropsItem(Who=event.who.name.title(), item=event.item.name))
		elif isinstance(event, Event.MonsterConsumedItem):
			Events().trigger(ItemConsumed(item=event.item.name))
		elif isinstance(event, Event.Unwielding):
			Events().trigger(Unwielding(item=event.item.name))
		elif isinstance(event, Event.TakingOff):
			Events().trigger(TakingOff(item=event.item.name))
		elif isinstance(event, Event.Wielding):
			Events().trigger(Wielding(item=event.item.name))
		elif isinstance(event, Event.Wearing):
			Events().trigger(Wearing(item=event.item.name))
		elif isinstance(event, Event.NotWearable):
			Events().trigger(CannotWear(item=event.item.name))
		elif isinstance(event, Event.NotConsumable):
			Events().trigger(CannotConsume(item=event.item.name))
		elif isinstance(event, Event.WelcomeBack):
			trace.debug(event)
			Events().trigger(WelcomeBack(who=event.who.name))
		elif isinstance(event, Event.InventoryFull):
			Events().trigger(InventoryFull(item=event.item.name))
		elif isinstance(event, Event.GrabbedItem):
			Events().trigger(GrabbedItem(who=event.who.name, item=event.item.name))

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
		Events().trigger(GodModeSwitched(name=item.text, state='ON' if new_state else 'off'))
		return to_main_screen(self)

class ConsumeItem:
	def prompt(self): return "Which item to consume?"
	def item_action(self, index):
		item = self.data.rogue.inventory[index]
		self.data.history += self.data.rogue.consume(item)

class DropItem:
	def prompt(self): return "Which item to drop?"
	def item_action(self, index):
		item = self.data.rogue.inventory[index]
		self.data.history += self.data.current_level.drop_item(self.data.rogue, item)

class WieldItem:
	def prompt(self): return "Which item to wield?"
	def item_action(self, index):
		item = self.data.rogue.inventory[index]
		self.data.history += self.data.rogue.wield(item)

class WearItem:
	def prompt(self): return "Which item to wear?"
	def item_action(self, index):
		item = self.data.rogue.inventory[index]
		self.data.history += self.data.rogue.wear(item)

class QuickItemSelection(tui.widgets.Prompt):
	def extended_mode(self):
		raise NotImplementedError
	def choices(self):
		return [chr(ord('a') + i) for i in range(len(self.data.rogue.inventory))] + ['*']
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
		if not self.data.rogue.inventory:
			return "(empty)"
		return ""
	def items(self):
		for index, item in enumerate(self.data.rogue.inventory):
			line = "{0} {1}".format(item.sprite, item.name)
			if self.data.rogue.wielding == item:
				line += " (wielding)"
			if self.data.rogue.wearing == item:
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

def main(stdscr):
	curses.curs_set(0)

	with SerializedEntity(xdg.save_data_path('dotrogue')/'rogue.sav', Version._top(), entity_name='dungeon', unlink=True, readable=True) as savefile:
		if savefile.entity:
			dungeon = savefile.entity
			dungeon.generator = RogueDungeonGenerator()
			dungeon.history.append(Event.WelcomeBack(dungeon.rogue))
		else:
			dungeon = Dungeon(RogueDungeonGenerator(), Rogue)
			dungeon.go_to_level(0)
			dungeon.rogue.inventory.append(Dagger())
			savefile.reset(dungeon)

		game = Game(stdscr)
		return_code = game.run(to_main_screen(dotdict(data=dungeon)))
		if return_code is False:
			savefile.reset()

import click
@click.command()
@click.option('--debug', is_flag=True)
def cli(debug=False):
	if debug:
		trace.setLevel(logging.DEBUG)
	curses.wrapper(main)

if __name__ == '__main__':
	cli()
