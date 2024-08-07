from __future__ import absolute_import
from ._base import UI, Action
import curses
from ..messages import Log
from .. import messages
from ..game import Direction
from ..math import Point

class Curses(UI):
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
				else:
					events.append('{0}!'.format(event.obj.name))
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
		self.window.addstr(24, 0, (' '.join(status) + " " * 80)[:80])

		if self.aim:
			self.window.move(1+self.aim.y, self.aim.x)
		self.window.refresh()

		if not player:
			self.window.getch()
	def user_interrupted(self):
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

		if control == ord('q'):
			Log.debug('Exiting the game.')
			return Action.EXIT, None
		elif control == ord('x'):
			if self.aim:
				self.aim = None
				curses.curs_set(0)
			else:
				self.aim = game.get_player().pos
				curses.curs_set(1)
		elif self.aim and control == ord('.'):
			dest = self.aim
			self.aim = None
			curses.curs_set(0)
			return Action.WALK_TO, dest
		elif control == ord('o'):
			return Action.AUTOEXPLORE, None
		elif control == ord('~'):
			control = self.window.getch()
			if control == ord('v'):
				return Action.GOD_TOGGLE_VISION, None
			elif control == ord('c'):
				return Action.GOD_TOGGLE_NOCLIP, None
		elif control == ord('Q'):
			Log.debug('Suicide.')
			return Action.SUICIDE, None
		elif not self.aim and control == ord('>'):
			return Action.DESCEND, None
		elif control == ord('.'):
			return Action.WAIT, None
		elif control == ord('g'):
			return Action.GRAB, game.get_player().pos
		elif chr(control) in 'hjklyubn':
			Log.debug('Moving.')
			if self.aim:
				shift = {
					'h' : Point(-1,  0),
					'j' : Point( 0, +1),
					'k' : Point( 0, -1),
					'l' : Point(+1,  0),
					'y' : Point(-1, -1),
					'u' : Point(+1, -1),
					'b' : Point(-1, +1),
					'n' : Point(+1, +1),
					}[chr(control)]
				new_pos = self.aim + shift
				if game.strata.valid(new_pos):
					self.aim = new_pos
			else:
				direction = {
					'h' : Direction.LEFT,
					'j' : Direction.DOWN,
					'k' : Direction.UP,
					'l' : Direction.RIGHT,
					'y' : Direction.UP_LEFT,
					'u' : Direction.UP_RIGHT,
					'b' : Direction.DOWN_LEFT,
					'n' : Direction.DOWN_RIGHT,
					}[chr(control)]
				return Action.MOVE, direction
		return Action.NONE, None
