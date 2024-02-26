import sys
import logging
Log = logging.getLogger('rogue')
import curses
from clckwrkbdgr import xdg
import clckwrkbdgr.logging
from . import game

def cli():
	debug = '--debug' in sys.argv
	clckwrkbdgr.logging.init('rogue',
			debug=True,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			rewrite_file=not debug,
			stream=None,
			)
	Log.debug('started')
	game.run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
