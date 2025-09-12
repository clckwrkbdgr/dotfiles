import itertools
import logging
from clckwrkbdgr import xdg
from clckwrkbdgr.math import Point, Size, Rect
from clckwrkbdgr.fs import SerializedEntity
import clckwrkbdgr.tui
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.logging
trace = logging.getLogger('rogue')
import src.world.roguedungeon 
from clckwrkbdgr.pcg import RNG
import clckwrkbdgr.pcg.rogue
from src.engine.items import Item, Wearable, Consumable
from src.world.roguedungeon import Scene, Builder
from src.engine import events, actors, appliances, ui, Events, builders
from src.engine.entity import MakeEntity
from src.engine.ui import Sprite
from hud import *
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *
from world import *

VERSION = 666

def main(ui):
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'oldrogue.sav')
	with clckwrkbdgr.serialize.stream.AutoSavefile(savefile) as savefile:
		dungeon = Game()
		if savefile.reader:
			dungeon.load(savefile.reader)
		else:
			dungeon.generate('rogue/0')

		game = MainGame(dungeon)
		loop = clckwrkbdgr.tui.ModeLoop(ui)
		loop.run(game)
		if dungeon.is_finished():
			savefile.savefile.unlink()
		else:
			pass # savefile.save(dungeon, 666)

import click
@click.command()
@click.option('--debug', is_flag=True)
def cli(debug=False):
	clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	with clckwrkbdgr.tui.Curses() as ui:
		main(ui)

if __name__ == '__main__':
	cli()
