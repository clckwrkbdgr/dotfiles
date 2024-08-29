from __future__ import absolute_import
from ._base import UI, Action
import functools
from collections import namedtuple
import curses
from ..system.logging import Log
from .. import messages
from ..game import Game, Direction
from ..math import Point

class Keys:
	""" Keybingings registry. """
	Keybinding = namedtuple('Keybinding', 'key scancode callback param')
	KEYBINDINGS = {}
	MULTIKEYBINDINGS = {}
	@classmethod
	def bind(cls, key, param=None):
		""" Serves as decorator and binds key (or several keys) to action callback.
		Optional param may be passed to callback.
		If param is callable, it is called with argument of actual key name (useful in case of multikeys) and its result is used as an actual param instead.
		"""
		def _actual(f):
			if len(key) > 1:
				scancodes = tuple(ord(subkey) for subkey in key)
				cls.MULTIKEYBINDINGS[scancodes] = cls.Keybinding(key, scancodes, f, param)
			else:
				cls.KEYBINDINGS[ord(key)] = cls.Keybinding(key, ord(key), f, param)
			return f
		return _actual
	@classmethod
	def get(cls, scancode, bind_self=None):
		""" Returns callback for given scancode.
		If param is defined for the key, processes it automatically
		and returns closure with param bound as the last argument:
		keybinding.callback(..., param) -> callback(...)
		If bind_self is given, considers callback a method
		and binds it to the given instance.
		"""
		binding = cls.KEYBINDINGS.get(scancode)
		if not binding:
			binding = next((
				_binding for keys, _binding in cls.MULTIKEYBINDINGS.items()
				if scancode in keys
				), None)
		if not binding:
			return None
		callback = binding.callback
		if bind_self:
			callback = callback.__get__(bind_self, type(bind_self))
		param = binding.param
		if not param:
			return callback
		if callable(param):
			param = param(binding.key[binding.scancode.index(scancode)])
		def _bound_param(*args):
			args = args + (param,)
			return callback(*args)
		return _bound_param
	@classmethod
	def list_all(cls):
		""" Returns sorted list of all keybindings (multikeys first). """
		return sorted(cls.MULTIKEYBINDINGS.items()) + sorted(cls.KEYBINDINGS.items())

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

class Curses(UI):
	""" TUI using curses lib. """
	def __init__(self):
		self.window = None
		self.aim = None
	def __enter__(self): # pragma: no cover -- TODO Mostly repeats curses.wrapper - original wrapper has no context manager option.
		self.window = curses.initscr()
		curses.noecho()
		curses.cbreak()
		self.window.keypad(1)
		try:
			curses.start_color()
		except:
			pass
		# Custom actions.
		curses.curs_set(0)
		return self
	def __exit__(self, *_targs): # pragma: no cover -- TODO Mostly repeats curses.wrapper - original wrapper has no context manager option.
		self.window.keypad(0)
		curses.echo()
		curses.nocbreak()
		curses.endwin()
	def redraw(self, game):
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
			if isinstance(event, messages.DiscoverEvent):
				if event.obj == '>':
					events.append('exit!')
				elif hasattr(event.obj, 'name'):
					events.append('{0}!'.format(event.obj.name))
				else:
					events.append('{0}!'.format(event.obj))
			elif isinstance(event, messages.AttackEvent):
				events.append('{0} x> {1}.'.format(event.actor.name, event.target.name))
			elif isinstance(event, messages.HealthEvent):
				events.append('{0}{1:+}hp.'.format(event.target.name, event.diff))
			elif isinstance(event, messages.DeathEvent):
				events.append('{0} dies.'.format(event.target.name))
			elif isinstance(event, messages.MoveEvent):
				if event.actor != game.get_player():
					events.append('{0}...'.format(event.actor.name))
			elif isinstance(event, messages.DescendEvent):
				events.append('{0} V...'.format(event.actor.name))
			elif isinstance(event, messages.BumpEvent):
				if event.actor != game.get_player():
					events.append('{0} bumps.'.format(event.actor.name))
			elif isinstance(event, messages.GrabItemEvent):
				events.append('{0} ^^ {1}.'.format(event.actor.name, event.item.name))
			elif isinstance(event, messages.ConsumeItemEvent):
				events.append('{0} <~ {1}.'.format(event.actor.name, event.item.name))
			else:
				events.append('Unknown event {0}!'.format(repr(event)))
		self.window.addstr(0, 0, (' '.join(events) + " " * 80)[:80])

		status = []
		player = game.get_player()
		if player:
			status.append('hp: {0:>{1}}/{2}'.format(player.hp, len(str(player.species.max_hp)), player.species.max_hp))
			item = game.find_item(player.pos.x, player.pos.y)
			if item:
				status.append('here: {0}'.format(item.item_type.sprite))
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
			self.window.getch()
	def user_interrupted(self):
		""" Checks for key presses in nodelay mode. """
		self.window.nodelay(1)
		self.window.timeout(30)
		control = self.window.getch()
		self.window.nodelay(0)
		self.window.timeout(-1)
		return control != -1
	def user_action(self, game):
		Log.debug('Performing user actions.')
		control = self.window.getch()
		Log.debug('Control: {0} ({1}).'.format(control, repr(chr(control))))
		callback = Keys.get(control, bind_self=self)
		if callback:
			result = callback(game)
			if result is not None:
				return result
		return Action.NONE, None

	@Keys.bind('?')
	def help(self, game):
		""" Show this help. """
		self.window.clear()
		for row, (_, binding) in enumerate(Keys.list_all()):
			name = binding.callback.__doc__.strip()
			self.window.addstr(row, 0, '{0} - {1}'.format(binding.key, name))
		self.window.addstr(row + 1, 0, '[Press Any Key...]')
		self.window.refresh()
		self.window.getch()
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
		control = self.window.getch()
		if control == ord('v'):
			return Action.GOD_TOGGLE_VISION, None
		elif control == ord('c'):
			return Action.GOD_TOGGLE_NOCLIP, None
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
	@Keys.bind('hjklyubn', param=lambda key: DIRECTION[key])
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
