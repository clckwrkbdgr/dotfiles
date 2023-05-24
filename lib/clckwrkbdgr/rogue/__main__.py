import curses
from ..math import Point
from .dungeon import Dungeon

def main(stdscr):
	curses.curs_set(0)
	dungeon = Dungeon()
	controls = {ord(k):v for k,v in {
		'q' : SystemExit,
		'h' : Point(-1,  0),
		'j' : Point( 0, +1),
		'k' : Point( 0, -1),
		'l' : Point(+1,  0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),
		}.items()}
	while True:
		for y in range(25):
			for x in range(25):
				stdscr.addstr(y, x, dungeon.get_sprite((x, y)))
		stdscr.refresh()

		control = controls.get(stdscr.getch())
		if control is not None:
			try:
				dungeon.control(control)
			except SystemExit:
				break

if __name__ == '__main__':
	curses.wrapper(main)
