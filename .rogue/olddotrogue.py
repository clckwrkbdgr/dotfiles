from __future__ import print_function
import os, sys
import logging
Log = logging.getLogger('rogue')
from clckwrkbdgr import logging
import src.engine, src.engine.items, src.engine.actors, src.engine.terrain
import src.world.dungeons
from src.engine.ui import Sprite
from src.engine import ui
from src.engine.events import Events
from clckwrkbdgr.math import Point, Direction, Rect, Size
import src.world.dungeonbuilders
import clckwrkbdgr.fs
import src.engine.builders
import clckwrkbdgr.serialize.stream
from hud import *
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *
from world import *

class Game(src.engine.Game):
	def make_player(self):
		player = Rogue(None)
		player.fill_drops(self.rng)
		return player
	def make_scene(self, scene_id):
		return src.world.dungeons.Scene(self.rng, [
			BSPDungeon,
			CityBuilder,
			Sewers,
			RogueDungeon,
			CaveBuilder,
			MazeBuilder,
			])

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
@click.argument('command', required=False, type=click.Choice(['test']))
@click.argument('tests', nargs=-1)
def cli(debug=False, command=None, tests=None):
	if debug:
		clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename='rogue.log',
			stream=None,
			)
	savefile = clckwrkbdgr.serialize.stream.Savefile(os.path.expanduser('~/.rogue.sav'))
	def _need_tests():
		if command == 'test':
			return True
		if not savefile.exists():
			return False
		_last_save = savefile.last_save_time()
		for path in clckwrkbdgr.fs.find(
				'src', exclude_dir_names=['__pycache__'],
				exclude_extensions=['pyc'],
				):
			if path.stat().st_mtime > _last_save:
				return True
		return False
	if _need_tests():
		import subprocess, platform
		rc = subprocess.call(['unittest', '-p', 'py3'] + [arg for arg in tests if arg.startswith('src.')], shell=(platform.system() == 'Windows'))
		if rc != 0 or command == 'test':
			sys.exit(rc)
	Log.debug('started')
	with clckwrkbdgr.serialize.stream.AutoSavefile(savefile) as savefile:
		game = Game()
		if savefile.reader:
			game.load(savefile.reader)
		else:
			game.generate('dungeon')
		with clckwrkbdgr.tui.Curses() as ui:
			loop = clckwrkbdgr.tui.ModeLoop(ui)
			main_mode = MainGame(game)
			loop.run(main_mode)
		if not game.is_finished():
			savefile.save(game, src.game.Version.CURRENT)
		else:
			savefile.savefile.unlink()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
