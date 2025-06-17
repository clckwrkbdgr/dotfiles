import sys
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr import xdg, fs
from clckwrkbdgr import logging
import clckwrkbdgr.tui
from .dungeon import Dungeon
from .game import Game

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	with fs.SerializedEntity.store(xdg.save_data_path('dotrogue')/'rogue.sav', 'dungeon', Dungeon) as savefile:
		dungeon = Dungeon()
		if savefile.entity:
			dungeon.load(savefile.entity)
		else:
			dungeon.generate()
		game = Game(dungeon)
		with clckwrkbdgr.tui.Curses() as ui:
			clckwrkbdgr.tui.Mode.run(game, ui)
		if dungeon.is_finished():
			savefile.reset()
		else:
			game.save(savefile.entity)

if __name__ == '__main__':
	cli()
