import sys
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr import xdg, fs
from clckwrkbdgr import logging
from clckwrkbdgr.math import Point, Rect, Size
import clckwrkbdgr.tui
from src.world import endlessdungeon, endlessbuilders
from src import engine
from src.engine import ui, terrain, actors
from hud import *

class EndlessFloor(terrain.Terrain):
	_sprite = ui.Sprite('.', None)
	_name = '.'
	_passable = True
class EndlessWall(terrain.Terrain):
	_sprite = ui.Sprite('#', None)
	_name = '#'
	_passable = False
class EndlessVoid(terrain.Terrain):
	_sprite = ui.Sprite(' ', None)
	_name = ' '
	_passable = False

class Player(actors.Monster, actors.Player):
	_sprite = ui.Sprite("@", None)
	_vision = 20

class Scene(endlessdungeon.Scene):
	BUILDERS = lambda: endlessbuilders.Builders([
		endlessbuilders.FieldOfTanks,
		endlessbuilders.EmptySquare,
		endlessbuilders.FilledWithGarbage,
		],
					 void=EndlessVoid(),
					 floor=EndlessFloor(),
					 wall=EndlessWall(),
					 start=lambda:'start'
					 )

class Dungeon(engine.Game):
	def make_scene(self, scene_id):
		return Scene()
	def make_player(self):
		return Player(None)

class Game(ui.MainGame):
	VIEW_CENTER = Point(12, 12)
	INDICATORS = [
			(Point(27, 0), HUD.Time),
			(Point(27, 1), HUD.Pos),
			(Point(27, 24), HUD.Auto),
			]

	def get_viewrect(self):
		return Rect(self.game.scene.get_player().pos - self.VIEW_CENTER, Size(25, 25))
	def get_message_line_rect(self):
		return Rect(Point(0, 25), Size(80, 1))

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	logging.init('rogue',
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
		game = Game(dungeon)
		with clckwrkbdgr.tui.Curses() as ui:
			clckwrkbdgr.tui.Mode.run(game, ui)
		if dungeon.is_finished():
			savefile.reset()
		else:
			game.save(savefile.entity)

if __name__ == '__main__':
	cli()
