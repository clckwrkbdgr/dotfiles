import sys
import logging
trace = logging.getLogger('rogue')
from .. import xdg
from .. import logging
from .dungeon import Dungeon
from .ui import Curses
from .game import Game
from .util import stored_entity

if __name__ == '__main__':
	logging.init('rogue',
			debug='-d' in sys.argv,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	with stored_entity(xdg.save_data_path('dotrogue')/'rogue.sav', 'dungeon', Dungeon) as dungeon:
		game = Game(dungeon)
		gui = Curses(game)
		gui.run()
