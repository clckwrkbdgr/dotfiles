import sys
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr import xdg, fs
from clckwrkbdgr import logging
from clckwrkbdgr.math import Point, Rect, Size
import clckwrkbdgr.tui
from . import dungeon, builders
from ..engine import ui, actors

Keys = clckwrkbdgr.tui.Keymapping()
MOVEMENT = {
		'h' : Point(-1, 0),
		'j' : Point(0, 1),
		'k' : Point(0, -1),
		'l' : Point(1, 0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),
		}

class Player(actors.Monster):
	_sprite = ui.Sprite("@", None)

class Scene(dungeon.Scene):
	BUILDERS = builders.Builders

class Dungeon(dungeon.Dungeon):
	def make_scene(self, scene_id):
		return Scene()
	def make_player(self):
		return Player(None)

class Game(ui.MainGame):
	KEYMAPPING = Keys
	VIEW_CENTER = Point(12, 12)
	INDICATORS = [
			ui.Indicator(Point(27, 0), 29, lambda self:'Time: {0}'.format(self.game.time)),
			ui.Indicator(Point(27, 1), 29, lambda self:'X:{x} Y:{y}  '.format(x=self.game.scene.get_player().pos.x, y=self.game.scene.get_player().pos.y)),
			ui.Indicator(Point(27, 24), 29, lambda self:'[autoexploring, press ESC...]' if self.game.autoexplore else ''),
			]

	def get_viewrect(self):
		return Rect(self.game.scene.get_player().pos - self.VIEW_CENTER, Size(25, 25))
	def get_message_line_rect(self):
		return Rect(Point(0, 25), Size(80, 1))
	@Keys.bind('q')
	def quit(self):
		return True
	@Keys.bind('o')
	def start_autoexplore(self):
		self.game.automove()
	@Keys.bind(list('hjklyubn'), lambda key:MOVEMENT[str(key)])
	def move_player(self, control):
		self.game.move_actor(self.game.scene.get_player(), control)

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
			dungeon.generate(None)
		game = Game(dungeon)
		with clckwrkbdgr.tui.Curses() as ui:
			clckwrkbdgr.tui.Mode.run(game, ui)
		if dungeon.is_finished():
			savefile.reset()
		else:
			game.save(savefile.entity)

if __name__ == '__main__':
	cli()
