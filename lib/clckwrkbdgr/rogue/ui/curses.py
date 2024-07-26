from ._base import UI, Action
import curses
from ..messages import Log
from ..game import Direction
from ..math import Point

class Curses(UI): # pragma: no cover -- TODO
	def __init__(self):
		self.window = None
		self.aim = None
	def __enter__(self):
		# Mostly repeats curses.wrapper - original wrapper has no context manager option.
		self.window = curses.initscr()
		curses.noecho()
		curses.cbreak()
		self.window.keypad(1)
		try:
			curses.start_color()
		except:
			pass
		curses.curs_set(0)
		return self
	def __exit__(self, *_targs):
		# Mostly repeats curses.wrapper - original wrapper has no context manager option.
		self.window.keypad(0)
		curses.echo()
		curses.nocbreak()
		curses.endwin()
	def redraw(self, game):
		Log.debug('Redrawing interface.')
		Log.debug('Player at: {0}'.format(game.player))
		viewport = game.get_viewport()
		for row in range(viewport.height):
			for col in range(viewport.width):
				Log.debug('Cell {0},{1}'.format(col, row))
				sprite = game.get_sprite(col, row)
				self.window.addstr(1+row, col, sprite or ' ')

		status = []
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
				self.aim = game.player
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
