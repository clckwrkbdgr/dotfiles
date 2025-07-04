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

class Player(src.monsters.Monster):
	_name = 'player'
	_sprite = '@'
	max_hp = 10
	vision = 10
	drops = None

class Monster(src.monsters.Monster):
	_name = 'monster'
	_sprite = 'M'
	max_hp = 3
	vision = 10
	drops = None

class Plant(src.monsters.Monster):
	_name = 'plant'
	_sprite = 'P'
	max_hp = 1
	vision = 1
	drops = [
			(1, None),
			(5, 'healing potion'),
			]

class Slime(src.monsters.Monster):
	_name = 'slime'
	_sprite = 'o'
	max_hp = 5
	vision = 3
	drops = [
			(1, None),
			(1, 'healing potion'),
			]

class Rodent(src.monsters.Monster):
	_name = 'rodent'
	_sprite = 'r'
	max_hp = 3
	vision = 8
	drops = [
			(5, None),
			(1, 'healing potion'),
			]

class Potion(src.items.Item):
	_name = 'potion'
	_sprite = '!'
	effect = src.items.Effect.NONE

class HealingPotion(src.items.Item):
	_name = 'healing potion'
	_sprite = '!'
	effect = src.items.Effect.HEALING

class Void(src.terrain.Cell):
	_name = 'void'
	_sprite = ' '
	passable = False
class Corner(src.terrain.Cell):
	_name = 'corner'
	_sprite = "+"
	passable = False
	remembered='+'
class Door(src.terrain.Cell):
	_name = 'door'
	_sprite = "+"
	passable = True
	remembered='+'
class RogueDoor(src.terrain.Cell):
	_name = 'rogue_door'
	_sprite = "+"
	passable = True
	remembered='+'
	allow_diagonal=False
	dark=True
class Floor(src.terrain.Cell):
	_name = 'floor'
	_sprite = "."
	passable = True
class TunnelFloor(src.terrain.Cell):
	_name = 'tunnel_floor'
	_sprite = "."
	passable = True
	allow_diagonal=False
class Passage(src.terrain.Cell):
	_name = 'passage'
	_sprite = "#"
	passable = True
	remembered='#'
class RoguePassage(src.terrain.Cell):
	_name = 'rogue_passage'
	_sprite = "#"
	passable = True
	remembered='#'
	allow_diagonal=False
	dark=True
class Wall(src.terrain.Cell):
	_name = 'wall'
	_sprite = '#'
	passable = False
	remembered='#'
class WallH(src.terrain.Cell):
	_name = 'wall_h'
	_sprite = "-"
	passable = False
	remembered='-'
class WallV(src.terrain.Cell):
	_name = 'wall_v'
	_sprite = "|"
	passable = False
	remembered='|'
class Water(src.terrain.Cell):
	_name = 'water'
	_sprite = "~"
	passable = True

class DungeonMapping:
	void = Void()
	corner = Corner()
	door = Door()
	rogue_door = RogueDoor()
	floor = Floor()
	tunnel_floor = TunnelFloor()
	passage = Passage()
	rogue_passage = RoguePassage()
	wall = Wall()
	wall_h = WallH()
	wall_v = WallV()
	water = Water()

	@staticmethod
	def start(): return 'start'
	@staticmethod
	def exit(): return 'exit'

	@staticmethod
	def plant(pos,*data):
		return Plant(*(data + (pos,)))
	@staticmethod
	def slime(pos,*data):
		return Slime(*(data + (pos,)))
	@staticmethod
	def rodent(pos,*data):
		return Rodent(*(data + (pos,)))
	healing_potion = HealingPotion

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
			None : Void,
			'void' : Void,
			'corner' : Corner,
			'door' : Door,
			'rogue_door' : RogueDoor,
			'floor' : Floor,
			'tunnel_floor' : TunnelFloor,
			'passage' : Passage,
			'rogue_passage' : RoguePassage,
			'wall' : Wall,
			'wall_h' : WallH,
			'wall_v' : WallV,
			'water' : Water,
			'Void' : Void,
			'Corner' : Corner,
			'Door' : Door,
			'RogueDoor' : RogueDoor,
			'Floor' : Floor,
			'TunnelFloor' : TunnelFloor,
			'Passage' : Passage,
			'RoguePassage' : RoguePassage,
			'Wall' : Wall,
			'WallH' : WallH,
			'WallV' : WallV,
			'Water' : Water,
			}
	SPECIES = {
			'player' : Player,
			'monster' : Monster,
			'plant' : Plant,
			'slime' : Slime,
			'rodent' : Rodent,
			'Player' : Player,
			'Monster' : Monster,
			'Plant' : Plant,
			'Slime' : Slime,
			'Rodent' : Rodent,
			}
	ITEMS = {
			'potion' : Potion,
			'healing potion' : HealingPotion,
			'healing_potion' : HealingPotion,
			'Potion' : Potion,
			'HealingPotion' : HealingPotion,
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
