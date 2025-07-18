from __future__ import absolute_import
import functools
from collections import namedtuple
import curses, curses.ascii
import logging
Log = logging.getLogger('rogue')
from . import game
from clckwrkbdgr.math import Point, Direction, Rect
from clckwrkbdgr import utils
import clckwrkbdgr.tui
import clckwrkbdgr.text
from clckwrkbdgr.tui import Key, Keymapping
from .engine.events import Events

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
class MainGame(clckwrkbdgr.tui.Mode):
	KEYMAPPING = Keys
	def __init__(self, game):
		self.game = game
		self.aim = None
		self.messages = []

	def nodelay(self):
		return self.game.in_automovement()
	def redraw(self, ui):
		""" Redraws game completely. """
		game = self.game
		ui.cursor(bool(self.aim))
		Log.debug('Redrawing interface.')
		for pos, cell_info in game.scene.iter_cells(Rect(Point(0, 0), game.get_viewport())):
			cell, objects, items, monsters = cell_info
			sprite = ' '
			if game.god.vision or game.vision.field_of_view.is_visible(pos.x, pos.y):
				if monsters:
					sprite = monsters[-1].sprite
				elif items:
					sprite = items[-1].sprite
				elif objects:
					sprite = objects[-1]
				else:
					sprite = cell.sprite
			elif objects and game.vision.visited.cell(game.scene.exit_pos):
				sprite = '>'
			elif game.vision.visited.cell(pos) and cell.remembered:
				sprite = cell.remembered
			ui.print_char(pos.x, 1+pos.y, sprite or ' ')

		for callback, event in game.process_events(raw=True, bind_self=self):
			if not callback:
				self.messages.append('Unknown event {0}!'.format(repr(event)))
				continue
			result = callback(game, event)
			if not result:
				continue
			self.messages.append(result)
		if self.messages:
			to_remove, message_line = clckwrkbdgr.text.wrap_lines(self.messages, width=80)
			if not to_remove:
				del self.messages[:]
			elif to_remove > 0: # pragma: no cover -- TODO
				self.messages = self.messages[to_remove:]
			else: # pragma: no cover -- TODO
				self.messages[0] = self.messages[0][-to_remove:]
			ui.print_line(0, 0, (message_line + ' '*80)[:80])
		else:
			ui.print_line(0, 0, " " * 80)

		status = []
		player = game.scene.get_player()
		if player:
			status.append('hp: {0:>{1}}/{2}'.format(player.hp, len(str(player.max_hp)), player.max_hp))
			item = next(game.scene.iter_items_at(player.pos), None)
			if item:
				status.append('here: {0}'.format(item.sprite))
			if player.inventory:
				if len(player.inventory) <= 2:
					content = ''.join(item.sprite for item in player.inventory)
				else:
					content = len(player.inventory)
				status.append('inv: {0:>2}'.format(content))
		else:
			status.append('[DEAD] Press Any Key...')
		if game.movement_queue:
			status.append('[auto]')
		if game.god.vision:
			status.append('[vis]')
		if game.god.noclip:
			status.append('[clip]')
		ui.print_line(24, 0, (' '.join(status) + " " * 77)[:77] + '[?]')

		if self.aim:
			ui.cursor().move(self.aim.x, 1+self.aim.y)
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
	def on_discovering(self, game, event):
		if event.obj == '>':
			return 'exit!'
		elif hasattr(event.obj, 'name'):
			return '{0}!'.format(event.obj.name)
		else:
			return '{0}!'.format(event.obj)
	@Events.on(game.AttackEvent)
	def on_attack(self, game, event):
		return '{0} x> {1}.'.format(event.actor.name, event.target.name)
	@Events.on(game.HealthEvent)
	def on_health_change(self, game, event):
		return '{0}{1:+}hp.'.format(event.target.name, event.diff)
	@Events.on(game.DeathEvent)
	def on_death(self, game, event):
		return '{0} dies.'.format(event.target.name)
	@Events.on(game.MoveEvent)
	def on_movement(self, game, event):
		if event.actor != game.scene.get_player():
			return '{0}...'.format(event.actor.name)
	@Events.on(game.DescendEvent)
	def on_descending(self, game, event):
		return '{0} V...'.format(event.actor.name)
	@Events.on(game.BumpEvent)
	def on_bumping(self, game, event):
		if event.actor != game.scene.get_player():
			return '{0} bumps.'.format(event.actor.name)
	@Events.on(game.GrabItemEvent)
	def on_grabbing(self, game, event):
		return '{0} ^^ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.DropItemEvent)
	def on_dropping(self, game, event):
		return '{0} VV {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.ConsumeItemEvent)
	def on_consuming(self, game, event):
		return '{0} <~ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.EquipItemEvent)
	def on_equipping(self, game, event):
		return '{0} <+ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(game.UnequipItemEvent)
	def on_unequipping(self, game, event):
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
