import sys
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr import xdg, fs
import clckwrkbdgr.logging
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

class Scene(endlessdungeon.Scene):
	BUILDERS = lambda: endlessbuilders.Builders([
		endlessbuilders.FieldOfTanks,
		endlessbuilders.EmptySquare,
		endlessbuilders.FilledWithGarbage,
		],
					 void=Void(),
					 floor=Floor(),
					 wall=Wall(),
					 start=lambda:'start'
					 )

class Dungeon(engine.Game):
	def make_scene(self, scene_id):
		return Scene()
	def make_player(self):
		return Rogue(None)

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	with fs.SerializedEntity.store(xdg.save_data_path('dotrogue')/'endlessrogue.sav', 'dungeon', Dungeon) as savefile:
		dungeon = Dungeon()
		if hasattr(savefile, 'entity') and savefile.entity:
			dungeon.load(savefile.entity)
		else:
			dungeon.generate('endless')
		game = MainGame(dungeon)
		with clckwrkbdgr.tui.Curses() as ui:
			clckwrkbdgr.tui.Mode.run(game, ui)
		if dungeon.is_finished():
			savefile.reset()
		else:
			game.save(savefile.entity)

if __name__ == '__main__':
	cli()
