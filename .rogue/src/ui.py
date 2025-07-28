from __future__ import absolute_import
import functools
from collections import namedtuple
import curses, curses.ascii
import logging
Log = logging.getLogger('rogue')
from . import game
from clckwrkbdgr.math import Point, Direction, Rect, Size
from clckwrkbdgr import utils
import clckwrkbdgr.tui
import clckwrkbdgr.text
from clckwrkbdgr.tui import Key, Keymapping
from .engine.events import Events
from .engine import ui

DIRECTION = {
	'h' : Direction.LEFT,
	'j' : Direction.DOWN,
	'k' : Direction.UP,
	'l' : Direction.RIGHT,
	'y' : Direction.UP_LEFT,
	'u' : Direction.UP_RIGHT,
	'b' : Direction.DOWN_LEFT,
	'n' : Direction.DOWN_RIGHT,
	}

Keys = Keymapping()
class MainGame(ui.MainGame):
	KEYMAPPING = Keys
	INDICATORS = [
			ui.Indicator((0, 24), 11, lambda self: 'hp: {0:>{1}}/{2}'.format(
				self.game.scene.get_player().hp,
				len(str(self.game.scene.get_player().max_hp)),
				self.game.scene.get_player().max_hp) if self.game.scene.get_player() else '[DEAD] Press Any Key...'),
			ui.Indicator((12, 24), 7, lambda self: 'here: {0}'.format(
				next(self.game.scene.iter_items_at(self.game.scene.get_player().pos), None).sprite,
				) if self.game.scene.get_player() and next(self.game.scene.iter_items_at(self.game.scene.get_player().pos), None) else ''),
			ui.Indicator((20, 24), 7, lambda self: 'inv: {0:>2}'.format(
				''.join(item.sprite for item in self.game.scene.get_player().inventory)
				if len(self.game.scene.get_player().inventory) <= 2
				else len(self.game.scene.get_player().inventory)
				) if self.game.scene.get_player() and self.game.scene.get_player().inventory else ''
					 ),
			ui.Indicator((28, 24), 6, lambda self: '[auto]' if self.game.movement_queue else ''),
			ui.Indicator((34, 24), 5, lambda self: '[vis]' if self.game.god.vision else ''),
			ui.Indicator((39, 24), 6, lambda self: '[clip]' if self.game.god.noclip else ''),
			ui.Indicator((77, 24), 3, lambda self: '[?]'),
			]

	def nodelay(self):
		return self.game.in_automovement()
	def get_map_shift(self):
		return Point(0, 1)
	def get_viewrect(self):
		return self.game.get_viewport()
	def get_sprite(self, pos, cell_info):
		game = self.game
		cell, objects, items, monsters = cell_info
		sprite = ' '
		if game.god.vision or game.vision.field_of_view.is_visible(pos.x, pos.y):
			if monsters:
				sprite = monsters[-1].sprite
			elif items:
				sprite = items[-1].sprite
			elif objects:
				sprite = objects[-1].sprite
			else:
				sprite = cell.sprite
		elif objects and game.vision.visited.cell(pos):
			sprite = objects[-1].sprite
		elif game.vision.visited.cell(pos) and cell.remembered:
			sprite = cell.remembered
		return ui.Sprite(sprite or ' ', None)
	def get_message_line_rect(self):
		return Rect(Point(0, 0), Size(80, 1))
	def pre_action(self):
		return self.game._pre_action()
	def get_keymapping(self):
		return None if self.nodelay() else self.KEYMAPPING
	def action(self, control):
		if isinstance(control, clckwrkbdgr.tui.Key):
			self.game.autostop()
			return True
		return not control
	@Events.on(game.DiscoverEvent)
	def on_discovering(self, event):
		if hasattr(event.obj, 'name'):
			return '{0}!'.format(event.obj.name)
		else:
			return '{0}!'.format(event.obj)
	@Events.on(game.AttackEvent)
	def on_attack(self, event):
		return '{0} x> {1}.'.format(event.actor.name, event.target.name)
	@Events.on(game.HealthEvent)
	def on_health_change(self, event):
		return '{0}{1:+}hp.'.format(event.target.name, event.diff)
	@Events.on(game.DeathEvent)
	def on_death(self, event):
		return '{0} dies.'.format(event.target.name)
	@Events.on(game.MoveEvent)
	def on_movement(self, event):
		if event.actor != self.game.scene.get_player():
			return '{0}...'.format(event.actor.name)
	@Events.on(game.DescendEvent)
	def on_descending(self, event):
		return '{0} V...'.format(event.actor.name)
	@Events.on(game.BumpEvent)
	def on_bumping(self, event):
		if event.actor != self.game.scene.get_player():
			return '{0} bumps.'.format(event.actor.name)
	@Events.on(game.GrabItemEvent)
	def on_grabbing(self, event):
		return '{0} ^^ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.DropItemEvent)
	def on_dropping(self, event):
		return '{0} VV {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.ConsumeItemEvent)
	def on_consuming(self, event):
		return '{0} <~ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.NotConsumable)
	def on_not_consuming(self, event):
		return 'X {0}.'.format(event.item.name)
	@Events.on(game.EquipItemEvent)
	def on_equipping(self, event):
		return '{0} <+ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.UnequipItemEvent)
	def on_unequipping(self, event):
		return '{0} +> {1}.'.format(event.actor.name, event.item.name)

	@Keys.bind(None)
	def on_idle(self): # pragma: no cover -- TODO why is this needed?
		""" Show this help. """
		return None
	@Keys.bind('?')
	def help(self):
		""" Show this help. """
		return HelpScreen()
	@Keys.bind('q')
	def quit(self):
		""" Save and quit. """
		Log.debug('Exiting the game.')
		return True
	@Keys.bind('x')
	def examine(self):
		""" Examine surroundings (cursor mode). """
		if self.aim:
			self.aim = None
		else:
			self.aim = self.game.scene.get_player().pos
	@Keys.bind('.')
	def autowalk(self):
		""" Wait. """
		if self.aim:
			dest = self.aim
			self.aim = None
			self.game.walk_to(dest)
		else:
			self.game.wait()
			self.game.end_turn()
	@Keys.bind('o')
	def autoexplore(self):
		""" Autoexplore. """
		self.game.start_autoexploring()
	@Keys.bind('~')
	def god_mode(self):
		""" God mode options. """
		return GodModeMenu(self.game)
	@Keys.bind('Q')
	def suicide(self):
		""" Suicide (quit without saving). """
		Log.debug('Suicide.')
		self.game.suicide(self.game.scene.get_player())
		self.game.end_turn()
	@Keys.bind('>')
	def descend(self):
		""" Descend. """
		if not self.aim:
			self.game.descend()
	@Keys.bind('g')
	def grab(self):
		""" Grab item. """
		self.game.grab_item_at(self.game.scene.get_player(), self.game.scene.get_player().pos)
		self.game.end_turn()
	@Keys.bind('d')
	def drop(self):
		""" Drop item. """
		return DropSelection(self.game)
	@Keys.bind('e')
	def consume(self):
		""" Consume item. """
		return ConsumeSelection(self.game)
	@Keys.bind('i')
	def show_inventory(self):
		""" Show inventory. """
		return Inventory(self.game)
	@Keys.bind('E')
	def show_equipment(self):
		""" Show equipment. """
		return Equipment(self.game)
	@Keys.bind(list('hjklyubn'), param=lambda key: DIRECTION[str(key)])
	def move(self, direction):
		""" Move. """
		Log.debug('Moving.')
		if self.aim:
			shift = direction
			new_pos = self.aim + shift
			if self.game.scene.strata.valid(new_pos):
				self.aim = new_pos
		else:
			self.game.move(self.game.scene.get_player(), direction)
			self.game.end_turn()

class HelpScreen(clckwrkbdgr.tui.Mode):
	""" Main help screen with controls cheatsheet. """
	def redraw(self, ui):
		for row, (_, binding) in enumerate(Keys.list_all()):
			if utils.is_collection(binding.key):
				keys = ''.join(map(str, binding.key))
			else:
				keys = str(binding.key)
			ui.print_line(row, 0, '{0} - {1}'.format(keys, binding.help))
		ui.print_line(row + 1, 0, '[Press Any Key...]')
	def action(self, control):
		return False

GodModeKeys = Keymapping()
class GodModeMenu(clckwrkbdgr.tui.Mode):
	""" God mode options. """
	TRANSPARENT = True
	KEYMAPPING = GodModeKeys
	def __init__(self, game):
		self.game = game
	def redraw(self, ui):
		keys = ''.join([binding.key for _, binding in self.KEYMAPPING.list_all()])
		ui.print_line(0, 0, 'Select God option ({0})'.format(keys))
	def action(self, control):
		return False
	@GodModeKeys.bind('v')
	def vision(self):
		""" See all. """
		self.game.toggle_god_vision()
	@GodModeKeys.bind('c')
	def noclip(self):
		""" Walk through walls. """
		self.game.toggle_god_noclip()

InventoryKeys = Keymapping()
class Inventory(clckwrkbdgr.tui.Mode):
	""" Inventory menu.
	Supports prompting message.
	Initial prompt can be set via INITIAL_PROMPT.
	"""
	KEYMAPPING = InventoryKeys
	INITIAL_PROMPT = None
	def __init__(self, game):
		self.game = game
		self.prompt = self.INITIAL_PROMPT
	def redraw(self, ui):
		game = self.game
		inventory = game.scene.get_player().inventory
		if self.prompt:
			ui.print_line(0, 0, self.prompt)
		if not inventory:
			ui.print_line(1, 0, '(Empty)')
		else:
			for row, item in enumerate(inventory):
				ui.print_line(row + 1, 0, '{0} - {1}'.format(
					chr(ord('a') + row),
					item.name,
					))
	def action(self, done):
		return not done
	def _use(self, monster, item): # pragma: no cover
		return False
	@InventoryKeys.bind(list('abcdefghijlkmnopqrstuvwxyz'), param=lambda key:str(key))
	def select(self, param):
		""" Select item and close inventory. """
		if not self.game.scene.get_player().inventory:
			return None
		index = ord(param) - ord('a')
		if index >= len(self.game.scene.get_player().inventory):
			self.prompt = "No such item ({0})".format(param)
			return None
		if self._use(self.game.scene.get_player(), self.game.scene.get_player().inventory[index]):
			self.game.end_turn()
			return True
	@InventoryKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self):
		""" Close by Escape. """
		return True

EquipmentKeys = Keymapping()
class Equipment(clckwrkbdgr.tui.Mode):
	""" Equipment menu.
	"""
	KEYMAPPING = EquipmentKeys
	def __init__(self, game):
		self.game = game
		self.done = False
	def redraw(self, ui):
		game = self.game
		wielding = game.scene.get_player().wielding
		if wielding:
			wielding = wielding.name
		ui.print_line(0, 0, 'wielding [a] - {0}'.format(wielding))
	def action(self, done):
		return not (done or self.done)
	@EquipmentKeys.bind('a')
	def wield(self):
		""" Wield or unwield item. """
		if self.game.scene.get_player().wielding:
			self.game.unwield_item(self.game.scene.get_player())
			self.game.end_turn()
			return True
		self.done = True
		return WieldSelection(self.game)
	@EquipmentKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self):
		""" Close by Escape. """
		return True

class ConsumeSelection(Inventory):
	""" Select item to consume from inventory. """
	INITIAL_PROMPT = "Select item to consume:"
	def _use(self, monster, item):
		self.game.consume_item(monster, item)
		return True

class DropSelection(Inventory):
	""" Select item to drop from inventory. """
	INITIAL_PROMPT = "Select item to drop:"
	def _use(self, monster, item):
		""" Select item and close inventory. """
		self.game.drop_item(monster, item)
		return True

class WieldSelection(Inventory):
	""" Select item to wield from inventory. """
	INITIAL_PROMPT = "Select item to wield:"
	def _use(self, monster, item):
		self.game.wield_item(monster, item)
		return True
