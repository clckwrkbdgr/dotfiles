import logging
import clckwrkbdgr.logging
Log = logging.getLogger('rogue')
from clckwrkbdgr import xdg
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.tui
from src.engine import builders, scene
from src.engine import events, auto, vision
from hud import *
from world import *

SAVEFILE_VERSION = 18

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	Log.debug('started')
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'rogue.sav')
	with savefile.get_reader() as reader:
		game = Game()
		if reader:
			assert reader.version == SAVEFILE_VERSION, (reader.version, SAVEFILE_VERSION, savefile.filename)
			game.load(reader)
		else:
			game.generate('overworld')
	with clckwrkbdgr.tui.Curses() as ui:
		main_game = MainGame(game)
		loop = clckwrkbdgr.tui.ModeLoop(ui)
		loop.run(main_game)
	if game.is_finished():
		savefile.unlink()
	else:
		with savefile.save(SAVEFILE_VERSION) as writer:
			game.save(writer)
	Log.debug('exited')

if __name__ == '__main__':
	cli()
