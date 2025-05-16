from __future__ import print_function
import os, sys
import logging
Log = logging.getLogger('rogue')
import src.game, src.items, src.monsters, src.terrain
import src.ui
import src.pcg
import clckwrkbdgr.fs
import clckwrkbdgr.serialize.stream

class DungeonSquatters(src.pcg.settlers.WeightedSquatters):
	MONSTERS = [
			(1, 'plant', src.monsters.Behavior.DUMMY),
			(3, 'slime', src.monsters.Behavior.INERT),
			(10, 'rodent', src.monsters.Behavior.ANGRY),
			]
	ITEMS = [
			(1, 'healing potion',),
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
			None : src.terrain.Terrain('void', ' ', False),
			'corner' : src.terrain.Terrain('corner', "+", False, remembered='+'),
			'door' : src.terrain.Terrain('door', "+", True, remembered='+'),
			'rogue_door' : src.terrain.Terrain('rogue_door', "+", True, remembered='+', allow_diagonal=False, dark=True),
			'floor' : src.terrain.Terrain('floor', ".", True),
			'tunnel_floor' : src.terrain.Terrain('tunnel_floor', ".", True, allow_diagonal=False),
			'passage' : src.terrain.Terrain('passage', "#", True, remembered='#'),
			'rogue_passage' : src.terrain.Terrain('rogue_passage', "#", True, remembered='#', allow_diagonal=False, dark=True),
			'wall' : src.terrain.Terrain('wall', '#', False, remembered='#'),
			'wall_h' : src.terrain.Terrain('wall_h', "-", False, remembered='-'),
			'wall_v' : src.terrain.Terrain('wall_v', "|", False, remembered='|'),
			'water' : src.terrain.Terrain('water', "~", True),
			}
	SPECIES = {
			'player' : src.monsters.Species('player', "@", 10, vision=10),
			'monster' : src.monsters.Species('monster', "M", 3, vision=10),

			'plant' : src.monsters.Species('plant', "P", 1, vision=1, drops=[
				(1, None),
				(5, 'healing potion'),
				]),
			'slime' : src.monsters.Species('slime', "o", 5, vision=3, drops=[
				(1, None),
				(1, 'healing potion'),
				]),
			'rodent' : src.monsters.Species('rodent', "r", 3, vision=8, drops=[
				(5, None),
				(1, 'healing potion'),
				]),
			}
	ITEMS = {
			'potion' : src.items.ItemType('potion', '!', src.items.Effect.NONE),
			'healing potion' : src.items.ItemType('healing potion', '!', src.items.Effect.HEALING),
			}

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	savefile = clckwrkbdgr.serialize.stream.Savefile(os.path.expanduser('~/.rogue.sav'))
	def _need_tests():
		if 'test' in sys.argv:
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
		rc = subprocess.call(['unittest', '-p', 'py3'] + [arg for arg in sys.argv if arg.startswith('src.')], shell=(platform.system() == 'Windows'))
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)
	Log.debug('started')
	with clckwrkbdgr.serialize.stream.AutoSavefile(savefile) as savefile:
		game = Game(load_from_reader=savefile.reader)
		with clckwrkbdgr.tui.Curses() as ui:
			loop = clckwrkbdgr.tui.ModeLoop(ui)
			main_mode = src.ui.curses.MainMode(game)
			loop.run(main_mode)
			if game.needs_saving():
				savefile.save(game, src.game.Version.CURRENT)
	Log.debug('exited')

if __name__ == '__main__':
	cli()
