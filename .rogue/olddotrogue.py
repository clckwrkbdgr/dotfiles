from __future__ import print_function
import os, sys
import logging
Log = logging.getLogger('rogue')
import src.game, src.items, src.monsters, src.terrain
import src.ui
import src.pcg
import clckwrkbdgr.fs
import clckwrkbdgr.serialize.stream

class DungeonSquatters(src.pcg.WeightedSquatters):
	MONSTERS = [
			(1, ('plant', src.monsters.Behavior.DUMMY)),
			(3, ('slime', src.monsters.Behavior.INERT)),
			(10, ('rodent', src.monsters.Behavior.ANGRY)),
			]
	ITEMS = [
			(1, ('healing_potion',)),
			]

class DungeonMapping:
	void = src.terrain.Cell(src.terrain.Terrain('void', ' ', False))
	corner = src.terrain.Cell(src.terrain.Terrain('corner', "+", False, remembered='+'))
	door = src.terrain.Cell(src.terrain.Terrain('door', "+", True, remembered='+'))
	rogue_door = src.terrain.Cell(src.terrain.Terrain('rogue_door', "+", True, remembered='+', allow_diagonal=False, dark=True))
	floor = src.terrain.Cell(src.terrain.Terrain('floor', ".", True))
	tunnel_floor = src.terrain.Cell(src.terrain.Terrain('tunnel_floor', ".", True, allow_diagonal=False))
	passage = src.terrain.Cell(src.terrain.Terrain('passage', "#", True, remembered='#'))
	rogue_passage = src.terrain.Cell(src.terrain.Terrain('rogue_passage', "#", True, remembered='#', allow_diagonal=False, dark=True))
	wall = src.terrain.Cell(src.terrain.Terrain('wall', '#', False, remembered='#'))
	wall_h = src.terrain.Cell(src.terrain.Terrain('wall_h', "-", False, remembered='-'))
	wall_v = src.terrain.Cell(src.terrain.Terrain('wall_v', "|", False, remembered='|'))
	water = src.terrain.Cell(src.terrain.Terrain('water', "~", True))

	@staticmethod
	def start(pos): return (pos, 'start')
	@staticmethod
	def exit(pos): return (pos, 'exit')

	@staticmethod
	def plant(pos,*data):
		return src.monsters.Monster(src.monsters.Species('plant', "P", 1, vision=1, drops=[
		(1, None),
		(5, 'healing_potion'),
		]), *(data + (pos,)))
	@staticmethod
	def slime(pos,*data):
		return src.monsters.Monster(src.monsters.Species('slime', "o", 5, vision=3, drops=[
		(1, None),
		(1, 'healing_potion'),
		]), *(data + (pos,)))
	@staticmethod
	def rodent(pos,*data):
		return src.monsters.Monster(src.monsters.Species('rodent', "r", 3, vision=8, drops=[
		(5, None),
		(1, 'healing_potion'),
		]), *(data + (pos,)))
	healing_potion = lambda pos,*data: src.items.ItemAtPos(pos, src.items.Item(src.items.ItemType('healing potion', '!', src.items.Effect.HEALING), *data))

class BSPDungeon(src.pcg.BSPDungeon, DungeonSquatters):
	Mapping = DungeonMapping
	PASSABLE = ('floor',)
	pass
class CityBuilder(src.pcg.CityBuilder, DungeonSquatters):
	Mapping = DungeonMapping
	PASSABLE = ('floor',)
	pass
class Sewers(src.pcg.Sewers, DungeonSquatters):
	Mapping = DungeonMapping
	PASSABLE = ('floor',)
	pass
class RogueDungeon(src.pcg.RogueDungeon, DungeonSquatters):
	Mapping = DungeonMapping
	PASSABLE = ('floor',)
	pass
class CaveBuilder(src.pcg.CaveBuilder, DungeonSquatters):
	Mapping = DungeonMapping
	PASSABLE = ('floor',)
	pass
class MazeBuilder(src.pcg.MazeBuilder, DungeonSquatters):
	Mapping = DungeonMapping
	PASSABLE = ('floor',)
	pass

class Game(src.game.Game):
	BUILDERS = [
			BSPDungeon,
			CityBuilder,
			Sewers,
			RogueDungeon,
			CaveBuilder,
			MazeBuilder,
			]
	TERRAIN = {
			None : src.terrain.Terrain('void', ' ', False),
			'void' : src.terrain.Terrain('void', ' ', False),
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
			'healing_potion' : src.items.ItemType('healing potion', '!', src.items.Effect.HEALING),
			}

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
@click.argument('command', required=False, type=click.Choice(['test']))
@click.argument('tests', nargs=-1)
def cli(debug=False, command=None, tests=None):
	if debug:
		Log.init('rogue.log')
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
			game.generate()
		with clckwrkbdgr.tui.Curses() as ui:
			loop = clckwrkbdgr.tui.ModeLoop(ui)
			main_mode = src.ui.MainGame(game)
			loop.run(main_mode)
		if not game.is_finished():
			savefile.save(game, src.game.Version.CURRENT)
		else:
			savefile.savefile.unlink()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
