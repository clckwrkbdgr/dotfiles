from __future__ import print_function
import os, sys
from src.system.logging import Log
import src.game, src.items, src.monsters
import src.ui
import src.pcg
import src.system.savefile
from src.test.main import Tester

class DungeonSquatters(src.pcg.settlers.Squatters):
	MONSTERS = [
			('plant', src.monsters.Behavior.DUMMY),
			('slime', src.monsters.Behavior.INERT),
			('rodent', src.monsters.Behavior.ANGRY),
			]
	ITEMS = [
			('healing potion',),
			]

class Game(src.game.Game):
	BUILDERS = [
			src.pcg.builders.BSPDungeon,
			src.pcg.builders.CityBuilder,
			src.pcg.builders.Sewers,
			src.pcg.builders.RogueDungeon,
			src.pcg.builders.CaveBuilder,
			src.pcg.builders.MazeBuilder,
			]
	SETTLERS = [
			DungeonSquatters,
			]
	TERRAIN = {
			None : src.game.Terrain(' ', False),
			'corner' : src.game.Terrain("+", False, remembered='+'),
			'door' : src.game.Terrain("+", True, remembered='+'),
			'rogue_door' : src.game.Terrain("+", True, remembered='+', allow_diagonal=False, dark=True),
			'floor' : src.game.Terrain(".", True),
			'tunnel_floor' : src.game.Terrain(".", True, allow_diagonal=False),
			'passage' : src.game.Terrain("#", True, remembered='#'),
			'rogue_passage' : src.game.Terrain("#", True, remembered='#', allow_diagonal=False, dark=True),
			'wall' : src.game.Terrain('#', False, remembered='#'),
			'wall_h' : src.game.Terrain("-", False, remembered='-'),
			'wall_v' : src.game.Terrain("|", False, remembered='|'),
			'water' : src.game.Terrain("~", True),
			}
	SPECIES = {
			'player' : src.monsters.Species('player', "@", 10, vision=10),
			'monster' : src.monsters.Species('monster', "M", 3, vision=10),

			'plant' : src.monsters.Species('plant', "P", 1, vision=1),
			'slime' : src.monsters.Species('slime', "o", 5, vision=3),
			'rodent' : src.monsters.Species('rodent', "r", 3, vision=8),
			}
	ITEMS = {
			'potion' : src.items.ItemType('potion', '!', src.items.Effect.NONE),
			'healing potion' : src.items.ItemType('healing potion', '!', src.items.Effect.HEALING),
			}

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	tester = Tester(rootdir=os.path.dirname(__file__))
	if tester.need_tests(sys.argv, src.system.savefile.Savefile.last_save_time() if src.system.savefile.Savefile.exists() else -1, printer=print):
		tests = tester.get_tests(sys.argv)
		rc = tester.run(tests, debug=debug)
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)
	Log.debug('started')
	with src.system.savefile.AutoSavefile() as savefile:
		game = Game(load_from_reader=savefile.reader)
		with src.ui.auto_ui()() as ui:
			if game.main_loop(ui):
				savefile.save(game, src.game.Version.CURRENT)
	Log.debug('exited')

if __name__ == '__main__':
	cli()
