from __future__ import absolute_import
from ._base import UI, Action
import functools
from collections import namedtuple
import curses, curses.ascii
import logging
Log = logging.getLogger('rogue')
from .. import messages
from ..game import Game, Direction
from clckwrkbdgr.math import Point
from clckwrkbdgr import utils
import clckwrkbdgr.tui
from clckwrkbdgr.tui import Key, Keymapping

class Events:
	""" Registry of convertors of events to string representation for messages line. """
	_registry = {}
	@classmethod
	def on(cls, event_type):
		""" Registers callback for given event type. """
		def _actual(f):
			cls._registry[event_type] = f
			return f
		return _actual
	@classmethod
	def get(cls, event, bind_self=None):
		""" Returns callback for given event.
		If bind_self is given, considers callback a method
		and binds it to the given instance.
		"""
		callback = cls._registry.get(type(event))
		if not callback:
			return None
		if bind_self:
			callback = callback.__get__(bind_self, type(bind_self))
		return callback
	@classmethod
	def list_all_events(cls):
		return sorted(cls._registry.keys(), key=lambda cls: cls.__name__)

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

class SubMode(object):
	""" Base class for sub mode for the main game (menus, dialogs, some
	other additional screens).
	Set .done=True when done and ready to quit sub-mode.
	"""
	TRANSPARENT = False # If True, first draw the main game, then this mode on top of it.
	KEYMAPPING = None # Keymapping object for this mode.
	def __init__(self, ui):
		self.ui = ui
		self.window = ui.window
		self.done = False
	def redraw(self, game): # pragma: no cover
		""" Redefine to draw mode-related features on screen.
		May not affect the whole screen, see class field TRANSPARENT.
		"""
		raise NotImplementedError()
	def on_any_key(self): # pragma: no cover
		""" Redefine to process "any other key" action (not defined in the main
		keymapping). E.g. can set .done=True for one-time screens (Press Any Key).
		"""
		pass
	def user_action(self, game):
		""" Performs sub-mode actions.
		Note that every sub-mode action will still go to the game,
		so it has to explicitly return Action.NONE in case of some internal
		sub-mode operations that do not affect the game.
		If keymapping is not set, every action will close the mode.
		See also: on_any_key()
		"""
		Log.debug('Performing user actions.')
		if self.KEYMAPPING:
			control = self.ui.get_control(self.KEYMAPPING, bind_self=self, callback_args=(game,))
			if control is not None:
				return control
		else:
			self.ui.get_keypress()
			self.done = True
		self.on_any_key()
		return Action.NONE, None

Keys = Keymapping()

class Curses(UI, clckwrkbdgr.tui.Curses):
	""" TUI using curses lib. """
	def __init__(self):
		super(Curses, self).__init__()
		self.aim = None
		self.messages = []
		self.mode = None
	def redraw(self, game):
		""" Redraws current mode. """
		if self.mode is None or self.mode.TRANSPARENT:
			self.redraw_main(game)
		else:
			self.window.clear()
		if self.mode:
			self.mode.redraw(game)
	def redraw_main(self, game):
		""" Redraws game completely. """
		Log.debug('Redrawing interface.')
		viewport = game.get_viewport()
		for row in range(viewport.height):
			for col in range(viewport.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				sprite = game.get_sprite(col, row)
				self.window.addstr(1+row, col, sprite or ' ')

		events = []
		for event in game.events:
			callback = Events.get(event, bind_self=self)
			if not callback:
				events.append('Unknown event {0}!'.format(repr(event)))
				continue
			result = callback(game, event)
			if not result:
				continue
			events.append(result)
		events.extend(self.messages)
		self.messages[:] = []
		self.window.addstr(0, 0, (' '.join(events) + " " * 80)[:80])

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
		self.window.addstr(24, 0, (' '.join(status) + " " * 77)[:77] + '[?]')

		if self.aim:
			self.window.move(1+self.aim.y, self.aim.x)
		self.window.refresh()

		if not player:
			# Pause so that user can catch current state after character's death.
			self.get_keypress()
	@Events.on(messages.DiscoverEvent)
	def on_discovering(self, game, event):
		if event.obj == '>':
			return 'exit!'
		elif hasattr(event.obj, 'name'):
			return '{0}!'.format(event.obj.name)
		else:
			return '{0}!'.format(event.obj)
	@Events.on(messages.AttackEvent)
	def on_attack(self, game, event):
		return '{0} x> {1}.'.format(event.actor.name, event.target.name)
	@Events.on(messages.HealthEvent)
	def on_health_change(self, game, event):
		return '{0}{1:+}hp.'.format(event.target.name, event.diff)
	@Events.on(messages.DeathEvent)
	def on_death(self, game, event):
		return '{0} dies.'.format(event.target.name)
	@Events.on(messages.MoveEvent)
	def on_movement(self, game, event):
		if event.actor != game.get_player():
			return '{0}...'.format(event.actor.name)
	@Events.on(messages.DescendEvent)
	def on_descending(self, game, event):
		return '{0} V...'.format(event.actor.name)
	@Events.on(messages.BumpEvent)
	def on_bumping(self, game, event):
		if event.actor != game.get_player():
			return '{0} bumps.'.format(event.actor.name)
	@Events.on(messages.GrabItemEvent)
	def on_grabbing(self, game, event):
		return '{0} ^^ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(messages.DropItemEvent)
	def on_dropping(self, game, event):
		return '{0} VV {1}.'.format(event.actor.name, event.item.name)
	@Events.on(messages.ConsumeItemEvent)
	def on_consuming(self, game, event):
		return '{0} <~ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(messages.EquipItemEvent)
	def on_equipping(self, game, event):
		return '{0} <+ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(messages.UnequipItemEvent)
	def on_unequipping(self, game, event):
		return '{0} +> {1}.'.format(event.actor.name, event.item.name)
	def user_interrupted(self):
		""" Checks for key presses in nodelay mode. """
		control = self.get_keypress(nodelay=True, timeout=30)
		return control is not None
	def user_action(self, game):
		""" Performs user action in current mode.
		May start or quit sub-modes as a result.
		"""
		Log.debug('Performing user actions.')
		if self.mode:
			result = self.mode.user_action(game)
			if isinstance(result, SubMode):
				self.mode = result
				return Action.NONE, None
			action, param = result
			if self.mode.done:
				self.mode = None
			return action, param
		control = self.get_control(Keys, bind_self=self, callback_args=(game,))
		if control is not None:
			return control
		return Action.NONE, None

	@Keys.bind('?')
	def help(self, game):
		""" Show this help. """
		self.mode = HelpScreen(self)
	@Keys.bind('q')
	def quit(self, game):
		""" Save and quit. """
		Log.debug('Exiting the game.')
		return Action.EXIT, None
	@Keys.bind('x')
	def examine(self, game):
		""" Examine surroundings (cursor mode). """
		if self.aim:
			self.aim = None
			curses.curs_set(0)
		else:
			self.aim = game.get_player().pos
			curses.curs_set(1)
	@Keys.bind('.')
	def autowalk(self, game):
		""" Wait. """
		if self.aim:
			dest = self.aim
			self.aim = None
			curses.curs_set(0)
			return Action.WALK_TO, dest
		else:
			return Action.WAIT, None
	@Keys.bind('o')
	def autoexplore(self, game):
		""" Autoexplore. """
		return Action.AUTOEXPLORE, None
	@Keys.bind('~')
	def god_mode(self, game):
		""" God mode options. """
		self.mode = GodModeMenu(self)
	@Keys.bind('Q')
	def suicide(self, game):
		""" Suicide (quit without saving). """
		Log.debug('Suicide.')
		return Action.SUICIDE, None
	@Keys.bind('>')
	def descend(self, game):
		""" Descend. """
		if not self.aim:
			return Action.DESCEND, None
	@Keys.bind('g')
	def grab(self, game):
		""" Grab item. """
		return Action.GRAB, game.get_player().pos
	@Keys.bind('d')
	def drop(self, game):
		""" Drop item. """
		self.mode = DropSelection(self)
	@Keys.bind('e')
	def consume(self, game):
		""" Consume item. """
		self.mode = ConsumeSelection(self)
	@Keys.bind('i')
	def show_inventory(self, game):
		""" Show inventory. """
		self.mode = Inventory(self)
	@Keys.bind('E')
	def show_equipment(self, game):
		""" Show equipment. """
		self.mode = Equipment(self)
	@Keys.bind(list('hjklyubn'), param=lambda key: DIRECTION[str(key)])
	def move(self, game, direction):
		""" Move. """
		Log.debug('Moving.')
		if self.aim:
			shift = Game.SHIFT[direction]
			new_pos = self.aim + shift
			if game.strata.valid(new_pos):
				self.aim = new_pos
		else:
			return Action.MOVE, direction

class HelpScreen(SubMode):
	""" Main help screen with controls cheatsheet. """
	def redraw(self, game):
		for row, (_, binding) in enumerate(Keys.list_all()):
			if utils.is_collection(binding.key):
				keys = ''.join(map(str, binding.key))
			else:
				keys = str(binding.key)
			self.window.addstr(row, 0, '{0} - {1}'.format(keys, binding.help))
		self.window.addstr(row + 1, 0, '[Press Any Key...]')
		self.window.refresh()

GodModeKeys = Keymapping()
class GodModeMenu(SubMode):
	""" God mode options. """
	TRANSPARENT = True
	KEYMAPPING = GodModeKeys
	def redraw(self, game):
		keys = ''.join([binding.key for _, binding in self.KEYMAPPING.list_all()])
		self.window.addstr(0, 0, 'Select God option ({0})'.format(keys))
		self.window.refresh()
	def on_any_key(self):
		self.done = True
	@GodModeKeys.bind('v')
	def vision(self, game):
		""" See all. """
		self.done = True
		return Action.GOD_TOGGLE_VISION, None
	@GodModeKeys.bind('c')
	def noclip(self, game):
		""" Walk through walls. """
		self.done = True
		return Action.GOD_TOGGLE_NOCLIP, None

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
	def redraw(self, game):
		inventory = game.get_player().inventory
		if self.prompt:
			self.window.addstr(0, 0, self.prompt)
		if not inventory:
			self.window.addstr(1, 0, '(Empty)')
		else:
			for row, item in enumerate(inventory):
				self.window.addstr(row + 1, 0, '{0} - {1}'.format(
					chr(ord('a') + row),
					item.item_type.name,
					))
		self.window.refresh()
	@InventoryKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self, game):
		""" Close by Escape. """
		self.done = True
		return Action.NONE, None

EquipmentKeys = Keymapping()
class Equipment(SubMode):
	""" Equipment menu.
	"""
	KEYMAPPING = EquipmentKeys
	def redraw(self, game):
		wielding = game.get_player().wielding
		if wielding:
			wielding = wielding.item_type.name
		self.window.addstr(0, 0, 'wielding [a] - {0}'.format(wielding))
		self.window.refresh()
	@EquipmentKeys.bind('a')
	def wield(self, game):
		""" Wield or unwield item. """
		if game.get_player().wielding:
			self.done = True
			return Action.UNWIELD, None
		return WieldSelection(self.ui)
	@EquipmentKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self, game):
		""" Close by Escape. """
		self.done = True
		return Action.NONE, None

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
			return Action.NONE, None
		self.done = True
		return Action.CONSUME, game.get_player().inventory[index]
	@ConsumeSelectionKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def cancel(self, game):
		""" Cancel selection. """
		self.done = True
		return Action.NONE, None

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
			return Action.NONE, None
		self.done = True
		return Action.DROP, game.get_player().inventory[index]
	@DropSelectionKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def cancel(self, game):
		""" Cancel selection. """
		self.done = True
		return Action.NONE, None

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
			return Action.NONE, None
		self.done = True
		return Action.WIELD, game.get_player().inventory[index]
	@WieldSelectionKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def cancel(self, game):
		""" Cancel selection. """
		self.done = True
		return Action.NONE, None
