import sys
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr import xdg, fs
from clckwrkbdgr import logging
from .dungeon import Dungeon
from .ui import Curses
from .game import Game

if __name__ == '__main__':
	logging.init('rogue',
			debug='-d' in sys.argv,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	with fs.SerializedEntity.store(xdg.save_data_path('dotrogue')/'rogue.sav', 'dungeon', Dungeon) as dungeon:
		game = Game(dungeon)
		gui = Curses(game)
		with clckwrkbdgr.tui.Curses() as ui:
			return game.run(ui)
