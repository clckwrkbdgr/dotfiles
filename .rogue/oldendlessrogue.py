import sys
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr import xdg, fs, utils
import clckwrkbdgr.logging
import clckwrkbdgr.serialize.stream
from clckwrkbdgr.math import Point, Rect, Size
import clckwrkbdgr.tui
from src.world import endlessdungeon, endlessbuilders
from src import engine
from src.engine import ui, terrain, actors
from hud import *
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *
from world import *

VERSION = 666

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'endlessrogue.sav')
	with savefile.get_reader() as reader:
		dungeon = Game()
		if reader:
			dungeon.load(reader)
		else:
			dungeon.generate('hollow')
		game = MainGame(dungeon)
		with clckwrkbdgr.tui.Curses() as ui:
			clckwrkbdgr.tui.Mode.run(game, ui)
		if dungeon.is_finished():
			savefile.unlink()
		else:
			with savefile.save(VERSION) as writer:
				dungeon.save(writer)

if __name__ == '__main__':
	cli()
