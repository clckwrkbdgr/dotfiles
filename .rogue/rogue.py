import sys
import functools
import random
import math
import string
import logging
from collections import namedtuple
import curses
import clckwrkbdgr.logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Rect, Size, Matrix, sign, distance
from clckwrkbdgr.math.grid import NestedGrid
from clckwrkbdgr import xdg, utils
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.tui
from src import engine
from src.engine import builders, scene
from src.engine import events, auto, vision
import src.engine.actors, src.engine.items, src.engine.appliances, src.engine.terrain
from src.engine.items import Item
from src.engine.terrain import Terrain
from src.engine.actors import Monster, EquippedMonster
from src.engine import ui
from src.engine import ui as UI
from src.engine.ui import Sprite
from src.engine import Events
from src.world import overworld
from hud import *
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *
from world import *

SAVEFILE_VERSION = 17

Color = namedtuple('Color', 'fg attr dweller monster')
class Game(engine.Game):
	COLORS = {
			'black': Color(curses.COLOR_BLACK, 0, False, False),
			'red': Color(curses.COLOR_RED, 0, True, True),
			'green': Color(curses.COLOR_GREEN, 0, True, True),
			'blue': Color(curses.COLOR_BLUE, 0, True, True),
			'yellow': Color(curses.COLOR_YELLOW, 0, True, True),
			'cyan': Color(curses.COLOR_CYAN, 0, True, True),
			'magenta': Color(curses.COLOR_MAGENTA, 0, True, True),
			'white': Color(curses.COLOR_WHITE, 0, True, True),
			'bold_black': Color(curses.COLOR_BLACK, curses.A_BOLD, True, True),
			'bold_red': Color(curses.COLOR_RED, curses.A_BOLD, True, True),
			'bold_green': Color(curses.COLOR_GREEN, curses.A_BOLD, True, True),
			'bold_blue': Color(curses.COLOR_BLUE, curses.A_BOLD, True, True),
			'bold_yellow': Color(curses.COLOR_YELLOW, curses.A_BOLD, True, True),
			'bold_cyan': Color(curses.COLOR_CYAN, curses.A_BOLD, True, True),
			'bold_magenta': Color(curses.COLOR_MAGENTA, curses.A_BOLD, True, True),
			'bold_white': Color(curses.COLOR_WHITE, curses.A_BOLD, False, True),
			}
	def make_scene(self, scene_id):
		return overworld.Scene(utils.all_subclasses(OverBuilder))
	def make_player(self):
		return Rogue(None)

def main(ui):
	for name, color in Game.COLORS.items():
		ui.init_color(name, color.fg, color.attr)

	game = Game()
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'rogue.sav')
	with savefile.get_reader() as reader:
		if reader:
			assert reader.version == SAVEFILE_VERSION, (reader.version, SAVEFILE_VERSION, savefile.filename)
			game.load(reader)
		else:
			game.generate(None)

	main_game = MainGame(game)
	loop = clckwrkbdgr.tui.ModeLoop(ui)
	loop.run(main_game)
	if not game.is_finished():
		with savefile.save(SAVEFILE_VERSION) as writer:
			game.save(writer)
	else:
		savefile.unlink()

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	if debug:
		clckwrkbdgr.logging.init(
			'rogue', debug=True, filename='rogue.log', stream=None,
			)
	with clckwrkbdgr.tui.Curses() as ui:
		main(ui)

if __name__ == '__main__':
	cli()
