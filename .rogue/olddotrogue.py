from __future__ import print_function
import os, sys
import logging
Log = logging.getLogger('rogue')
import src.game, src.engine.items, src.engine.actors, src.engine.terrain
import src.ui
from src.engine.ui import Sprite
import src.pcg
import clckwrkbdgr.fs
import src.engine.builders
import clckwrkbdgr.serialize.stream

class DungeonSquatters(src.engine.builders.Builder):
	""" Set of squatters, randomly distributed throughout the map
	based on their relative weights (int or float) within corresponding
	distribution list.

	Data should be defined in class fields MONSTERS and ITEMS as lists of tuples:
	MONSTERS = (<weight>, 'monster_type_id', <args...>)
	ITEMS = (<weight>, 'item_type_id', <args...>)

	Distribution is controlled by corresponding CELLS_PER_* fields, which should
	set amount of _free_ (i.e. passable) cells that support one monster/item.
	"""
	CELLS_PER_MONSTER = 60 # One monster for every 60 cells.
	MONSTERS = [
			(1, ('plant',)),
			(3, ('slime',)),
			(10, ('rodent',)),
			]
	CELLS_PER_ITEM = 180 # One item for every 180 cells.
	ITEMS = [
			(1, ('healing_potion',)),
			]
	def is_open(self, pos):
		return self.grid.cell(pos) == 'floor'
	def generate_actors(self):
		""" Places random population of different types of monsters.
		"""
		for _ in self.distribute(src.engine.builders.WeightedDistribution, self.MONSTERS, self.amount_by_free_cells(self.CELLS_PER_MONSTER)):
			yield _
	def generate_items(self):
		""" Drops items in random locations. """
		for _ in self.distribute(src.engine.builders.WeightedDistribution, self.ITEMS, self.amount_by_free_cells(self.CELLS_PER_ITEM)):
			yield _

class Potion(src.engine.items.Item):
	_name = 'potion'
	_sprite = Sprite('!', None)

class Healing(src.engine.items.Consumable):
	healing = 0
	def consume(self, target):
		diff = target.affect_health(self.healing)
		return [HealthEvent(target, diff)]

class HealingPotion(src.engine.items.Item, Healing):
	_name = 'healing potion'
	_sprite = Sprite('!', None)
	healing = +5

class Player(src.game.Player):
	_hostile_to = [src.engine.actors.Monster]
	_name = 'player'
	_sprite = Sprite('@', None)
	_max_hp = 10
	_vision = 10
	_attack = 1
	_max_inventory = 26

class Monster(src.engine.actors.Monster):
	_hostile_to = [Player]
	_name = 'monster'
	_sprite = Sprite('M', None)
	_max_hp = 3
	_vision = 10
	_attack = 1
	_max_inventory = 5

class Plant(src.engine.actors.Monster):
	_hostile_to = [Player]
	_name = 'plant'
	_sprite = Sprite('P', None)
	_max_hp = 1
	_vision = 1
	_attack = 1
	_max_inventory = 5
	_drops = [
			(1, None),
			(5, HealingPotion),
			]

class Slime(src.game.Inert):
	_hostile_to = [Player]
	_name = 'slime'
	_sprite = Sprite('o', None)
	_max_hp = 5
	_vision = 3
	_attack = 1
	_max_inventory = 5
	_drops = [
			(1, None),
			(1, HealingPotion),
			]

class Rodent(src.game.Angry):
	_hostile_to = [Player]
	_name = 'rodent'
	_sprite = Sprite('r', None)
	_max_hp = 3
	_vision = 8
	_attack = 1
	_max_inventory = 5
	_drops = [
			(5, None),
			(1, HealingPotion),
			]

class Void(src.engine.terrain.Terrain):
	_name = 'void'
	_sprite = Sprite(' ', None)
	_passable = False
class Corner(src.engine.terrain.Terrain):
	_name = 'corner'
	_sprite = Sprite("+", None)
	_passable = False
	_remembered='+'
class Door(src.engine.terrain.Terrain):
	_name = 'door'
	_sprite = Sprite("+", None)
	_passable = True
	_remembered='+'
class RogueDoor(src.engine.terrain.Terrain):
	_name = 'rogue_door'
	_sprite = Sprite("+", None)
	_passable = True
	_remembered='+'
	_allow_diagonal=False
	_dark=True
class Floor(src.engine.terrain.Terrain):
	_name = 'floor'
	_sprite = Sprite(".", None)
	_passable = True
class TunnelFloor(src.engine.terrain.Terrain):
	_name = 'tunnel_floor'
	_sprite = Sprite(".", None)
	_passable = True
	_allow_diagonal=False
class Passage(src.engine.terrain.Terrain):
	_name = 'passage'
	_sprite = Sprite("#", None)
	_passable = True
	_remembered='#'
class RoguePassage(src.engine.terrain.Terrain):
	_name = 'rogue_passage'
	_sprite = Sprite("#", None)
	_passable = True
	_remembered='#'
	_allow_diagonal=False
	_dark=True
class Wall(src.engine.terrain.Terrain):
	_name = 'wall'
	_sprite = Sprite('#', None)
	_passable = False
	_remembered='#'
class WallH(src.engine.terrain.Terrain):
	_name = 'wall_h'
	_sprite = Sprite("-", None)
	_passable = False
	_remembered='-'
class WallV(src.engine.terrain.Terrain):
	_name = 'wall_v'
	_sprite = Sprite("|", None)
	_passable = False
	_remembered='|'
class Water(src.engine.terrain.Terrain):
	_name = 'water'
	_sprite = Sprite("~", None)
	_passable = True

class Stairs(src.game.LevelExit):
	_name = 'stairs'
	_sprite = Sprite('>', None)

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
	def exit(): return Stairs()

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
class CityBuilder(src.pcg.CityBuilder, DungeonSquatters):
	Mapping = DungeonMapping
class Sewers(src.pcg.Sewers, DungeonSquatters):
	Mapping = DungeonMapping
class RogueDungeon(src.pcg.RogueDungeon, DungeonSquatters):
	Mapping = DungeonMapping
class CaveBuilder(src.pcg.CaveBuilder, DungeonSquatters):
	Mapping = DungeonMapping
class MazeBuilder(src.pcg.MazeBuilder, DungeonSquatters):
	Mapping = DungeonMapping

class Game(src.game.Game):
	BUILDERS = [
			BSPDungeon,
			CityBuilder,
			Sewers,
			RogueDungeon,
			CaveBuilder,
			MazeBuilder,
			]
	PLAYER_CLASS = Player

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
