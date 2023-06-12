import sys
import random
import curses
import logging
trace = logging.getLogger('rogue')
from .. import logging
from ..fs import SerializedEntity
from .. import xdg
from ..math import Point
from .dungeon import Dungeon

def main(stdscr):
	logging.init('rogue',
			debug='-d' in sys.argv,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	curses.curs_set(0)
	with SerializedEntity(xdg.save_data_path('dotrogue')/'rogue.sav', 0, entity_name='dungeon', unlink=False, readable=True) as savefile:
		if savefile.entity:
			dungeon = savefile.entity
		else:
			dungeon = Dungeon()
			savefile.reset(dungeon)
		run(stdscr, dungeon)

def run(stdscr, dungeon):
	controls = {ord(k):v for k,v in {
		'q' : SystemExit,
		'o' : 'autoexplore',
		'h' : Point(-1,  0),
		'j' : Point( 0, +1),
		'k' : Point( 0, -1),
		'l' : Point(+1,  0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),
		}.items()}
	controls[-1] = 'autoexplore'
	controls[27] = 'ESC'
	view_center = Point(12, 12)
	autoexplore = False
	game_time = 0
	while True:
		for y in range(-view_center.y, 25 - view_center.y):
			for x in range(-view_center.x, 25 - view_center.x):
				stdscr.addstr(view_center.y + y, view_center.x + x, dungeon.get_sprite((x, y)))
		stdscr.addstr(0, 27, 'Time: {0}'.format(game_time))
		stdscr.addstr(1, 27, 'X:{x} Y:{y}'.format(x=dungeon.rogue.x, y=dungeon.rogue.y))
		stdscr.addstr(24, 27, '[autoexploring, press ESC...]' if autoexplore else '                             ')
		stdscr.refresh()

		game_time += 1
		char = stdscr.getch()
		control = controls.get(char)
		trace.debug('Curses char: {0}'.format(repr(char)))
		trace.debug('Control: {0}'.format(repr(control)))
		trace.debug('Autoexplore={0}'.format(autoexplore))
		if control is not None:
			if control == 'autoexplore':
				if autoexplore:
					control = controls.get(ord(random.choice('hjklyubn')))
					trace.debug('Autoexploring: {0}'.format(repr(control)))
				else:
					trace.debug('Starting autoexplore.')
					autoexplore = True
					stdscr.nodelay(1)
					stdscr.timeout(100)
					continue
			elif control == 'ESC':
				trace.debug('Stopping autoexplore.')
				autoexplore = False
				stdscr.timeout(-1)
				stdscr.nodelay(0)
				continue
			try:
				dungeon.control(control)
			except SystemExit:
				trace.debug('Exiting...')
				break

if __name__ == '__main__':
	curses.wrapper(main)
