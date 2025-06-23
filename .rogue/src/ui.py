from __future__ import absolute_import
from .defs import Action
import functools
from collections import namedtuple
import curses, curses.ascii
import logging
Log = logging.getLogger('rogue')
from . import game
from clckwrkbdgr.math import Point, Direction
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

class SubMode(clckwrkbdgr.tui.Mode):
	""" Base class for sub mode for the main game (menus, dialogs, some
	other additional screens).
	Set .done=True when done and ready to quit sub-mode.
	"""
	def __init__(self, game):
		self.game = game
		self.done = False
	def redraw(self, ui): # pragma: no cover
		""" Redefine to draw mode-related features on screen.
		May not affect the whole screen, see class field TRANSPARENT.
		"""
		raise NotImplementedError()
	def on_any_key(self): # pragma: no cover
		""" Redefine to process "any other key" action (not defined in the main
		keymapping). E.g. can set .done=True for one-time screens (Press Any Key).
		"""
		pass
	def pre_action(self):
		return self.game._pre_action()
	def get_bind_callback_args(self):
		return (self.game,)
	def get_keymapping(self):
		return None if self.nodelay() else self.KEYMAPPING
	def action(self, control):
		""" Performs user action in current mode.
		May start or quit sub-modes as a result.
		Note that every sub-mode action will still go to the game,
		so it has to explicitly return Action.NONE in case of some internal
		sub-mode operations that do not affect the game.
		If keymapping is not set, every action will close the mode.
		See also: on_any_key()
		"""
		self.on_any_key()
		if isinstance(control, clckwrkbdgr.tui.Key):
			self.game.autostop()
		return not self.done

Keys = Keymapping()
class MainGame(SubMode):
	KEYMAPPING = Keys
	def __init__(self, *args, **kwargs):
		super(MainGame, self).__init__(*args, **kwargs)
		self.aim = None
		self.messages = []

	def nodelay(self):
		return self.game.in_automovement()
	def redraw(self, ui):
		""" Redraws game completely. """
		game = self.game
		ui.cursor(bool(self.aim))
		Log.debug('Redrawing interface.')
		viewport = game.get_viewport()
		for row in range(viewport.height):
			for col in range(viewport.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				sprite = game.get_sprite(col, row)
				ui.print_char(col, 1+row, sprite or ' ')

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
				self.messages = self.messages[self.to_remove:]
			else: # pragma: no cover -- TODO
				self.messages[0] = self.messages[0][-to_remove:]
			ui.print_line(0, 0, (message_line + ' '*80)[:80])
		else:
			ui.print_line(0, 0, " " * 80)

		status = []
		player = game.get_player()
		if player:
			status.append('hp: {0:>{1}}/{2}'.format(player.hp, len(str(player.species.max_hp)), player.species.max_hp))
			item = game.find_item(player.pos.x, player.pos.y)
			if item:
				status.append('here: {0}'.format(item.item_type.sprite))
			if player.inventory:
				if len(player.inventory) <= 2:
					content = ''.join(item.item_type.sprite for item in player.inventory)
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
		if event.actor != game.get_player():
			return '{0}...'.format(event.actor.name)
	@Events.on(game.DescendEvent)
	def on_descending(self, game, event):
		return '{0} V...'.format(event.actor.name)
	@Events.on(game.BumpEvent)
	def on_bumping(self, game, event):
		if event.actor != game.get_player():
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
	def on_idle(self, game): # pragma: no cover -- TODO why is this needed?
		""" Show this help. """
		return None
	@Keys.bind('?')
	def help(self, game):
		""" Show this help. """
		return HelpScreen(game)
	@Keys.bind('q')
	def quit(self, game):
		""" Save and quit. """
		Log.debug('Exiting the game.')
		self.done = True
	@Keys.bind('x')
	def examine(self, game):
		""" Examine surroundings (cursor mode). """
		if self.aim:
			self.aim = None
		else:
			self.aim = game.get_player().pos
	@Keys.bind('.')
	def autowalk(self, game):
		""" Wait. """
		if self.aim:
			dest = self.aim
			self.aim = None
			self.game.walk_to(dest)
		else:
			game.wait()
	@Keys.bind('o')
	def autoexplore(self, game):
		""" Autoexplore. """
		game.start_autoexploring()
	@Keys.bind('~')
	def god_mode(self, game):
		""" God mode options. """
		return GodModeMenu(game)
	@Keys.bind('Q')
	def suicide(self, game):
		""" Suicide (quit without saving). """
		Log.debug('Suicide.')
		self.game.suicide()
	@Keys.bind('>')
	def descend(self, game):
		""" Descend. """
		if not self.aim:
			game.descend()
	@Keys.bind('g')
	def grab(self, game):
		""" Grab item. """
		self.game.player_grab(game.get_player().pos)
	@Keys.bind('d')
	def drop(self, game):
		""" Drop item. """
		return DropSelection(game)
	@Keys.bind('e')
	def consume(self, game):
		""" Consume item. """
		return ConsumeSelection(game)
	@Keys.bind('i')
	def show_inventory(self, game):
		""" Show inventory. """
		return Inventory(game)
	@Keys.bind('E')
	def show_equipment(self, game):
		""" Show equipment. """
		return Equipment(game)
	@Keys.bind(list('hjklyubn'), param=lambda key: DIRECTION[str(key)])
	def move(self, game, direction):
		""" Move. """
		Log.debug('Moving.')
		if self.aim:
			shift = direction
			new_pos = self.aim + shift
			if game.strata.valid(new_pos):
				self.aim = new_pos
		else:
			game.move_player(direction)

class HelpScreen(SubMode):
	""" Main help screen with controls cheatsheet. """
	def redraw(self, ui):
		for row, (_, binding) in enumerate(Keys.list_all()):
			if utils.is_collection(binding.key):
				keys = ''.join(map(str, binding.key))
			else:
				keys = str(binding.key)
			ui.print_line(row, 0, '{0} - {1}'.format(keys, binding.help))
		ui.print_line(row + 1, 0, '[Press Any Key...]')
	def on_any_key(self):
		self.done = True
		return True

GodModeKeys = Keymapping()
class GodModeMenu(SubMode):
	""" God mode options. """
	TRANSPARENT = True
	KEYMAPPING = GodModeKeys
	def redraw(self, ui):
		keys = ''.join([binding.key for _, binding in self.KEYMAPPING.list_all()])
		ui.print_line(0, 0, 'Select God option ({0})'.format(keys))
	def on_any_key(self):
		self.done = True
		return True
	@GodModeKeys.bind('v')
	def vision(self, game):
		""" See all. """
		self.done = True
		game.toggle_god_vision()
	@GodModeKeys.bind('c')
	def noclip(self, game):
		""" Walk through walls. """
		self.done = True
		game.toggle_god_noclip()

InventoryKeys = Keymapping()
class Inventory(SubMode):
	""" Inventory menu.
	Supports prompting message.
	Initial prompt can be set via INITIAL_PROMPT.
	"""
	KEYMAPPING = InventoryKeys
	INITIAL_PROMPT = None
	def __init__(self, *args, **kwargs):
		super(Inventory, self).__init__(*args, **kwargs)
		self.prompt = self.INITIAL_PROMPT
	def redraw(self, ui):
		game = self.game
		inventory = game.get_player().inventory
		if self.prompt:
			ui.print_line(0, 0, self.prompt)
		if not inventory:
			ui.print_line(1, 0, '(Empty)')
		else:
			for row, item in enumerate(inventory):
				ui.print_line(row + 1, 0, '{0} - {1}'.format(
					chr(ord('a') + row),
					item.item_type.name,
					))
	@InventoryKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self, game):
		""" Close by Escape. """
		self.done = True

EquipmentKeys = Keymapping()
class Equipment(SubMode):
	""" Equipment menu.
	"""
	KEYMAPPING = EquipmentKeys
	def redraw(self, ui):
		game = self.game
		wielding = game.get_player().wielding
		if wielding:
			wielding = wielding.item_type.name
		ui.print_line(0, 0, 'wielding [a] - {0}'.format(wielding))
	@EquipmentKeys.bind('a')
	def wield(self, game):
		""" Wield or unwield item. """
		self.done = True
		if game.get_player().wielding:
			game.player_unwield()
			return
		return WieldSelection(game)
	@EquipmentKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self, game):
		""" Close by Escape. """
		self.done = True

ConsumeSelectionKeys = Keymapping()
class ConsumeSelection(Inventory):
	""" Select item to consume from inventory. """
	KEYMAPPING = ConsumeSelectionKeys
	INITIAL_PROMPT = "Select item to consume:"
	@ConsumeSelectionKeys.bind(list('abcdefghijlkmnopqrstuvwxyz'), param=lambda key:str(key))
	def select(self, game, param):
		""" Select item and close inventory. """
		index = ord(param) - ord('a')
		if index >= len(game.get_player().inventory):
			self.prompt = "No such item ({0})".format(param)
			return None
		self.done = True
		game.player_consume(game.get_player().inventory[index])
	@ConsumeSelectionKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def cancel(self, game):
		""" Cancel selection. """
		self.done = True

DropSelectionKeys = Keymapping()
class DropSelection(Inventory):
	""" Select item to drop from inventory. """
	KEYMAPPING = DropSelectionKeys
	INITIAL_PROMPT = "Select item to drop:"
	@DropSelectionKeys.bind(list('abcdefghijlkmnopqrstuvwxyz'), param=lambda key:str(key))
	def select(self, game, param):
		""" Select item and close inventory. """
		index = ord(param) - ord('a')
		if index >= len(game.get_player().inventory):
			self.prompt = "No such item ({0})".format(param)
			return None
		self.done = True
		game.player_drop(game.get_player().inventory[index])
	@DropSelectionKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def cancel(self, game):
		""" Cancel selection. """
		self.done = True

WieldSelectionKeys = Keymapping()
class WieldSelection(Inventory):
	""" Select item to wield from inventory. """
	KEYMAPPING = WieldSelectionKeys
	INITIAL_PROMPT = "Select item to wield:"
	@WieldSelectionKeys.bind(list('abcdefghijlkmnopqrstuvwxyz'), param=lambda key:str(key))
	def select(self, game, param):
		""" Select item and close inventory. """
		index = ord(param) - ord('a')
		if index >= len(game.get_player().inventory):
			self.prompt = "No such item ({0})".format(param)
			return None
		self.done = True
		game.player_wield(game.get_player().inventory[index])
	@WieldSelectionKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def cancel(self, game):
		""" Cancel selection. """
		self.done = True
