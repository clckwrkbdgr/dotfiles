import itertools
import logging
from clckwrkbdgr import xdg
from clckwrkbdgr.math import Point, Size, Rect
from clckwrkbdgr.fs import SerializedEntity
import clckwrkbdgr.tui
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.logging
trace = logging.getLogger('rogue')
import src.world.roguedungeon 
from clckwrkbdgr.pcg import RNG
import clckwrkbdgr.pcg.rogue
from src.engine.items import Item, Wearable, Consumable
from src.world.roguedungeon import Scene
from src.engine import events, actors, appliances, ui, Events, builders
from src.engine.entity import MakeEntity
from src.engine.ui import Sprite
from hud import *
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *

VERSION = 666

events.Events.on(Events.NeedKey)(lambda event:"You cannot escape the dungeon without {0}!".format(event.key))

class _Builder(builders.Builder):
	class Mapping(TerrainMapping, QuestMapping, ItemMapping, MonsterMapping, ObjectMapping):
		pass
	def __init__(self, depth, is_bottom, *args, **kwargs):
		self.depth = depth
		self.is_bottom = is_bottom
		super().__init__(*args, **kwargs)
	def fill_grid(self, grid):
		self.dungeon = clckwrkbdgr.pcg.rogue.Dungeon(self.rng, self.size, Size(3, 3), Size(4, 4))
		self.dungeon.generate_rooms()
		self.dungeon.generate_maze()
		self.dungeon.generate_tunnels()
		grid.clear('void')
		grid.set_cell((0, 1), 'corner')
		grid.set_cell((0, 2), 'wall_v')
		grid.set_cell((0, 3), 'wall_h')
		grid.set_cell((0, 4), 'floor')
		grid.set_cell((0, 5), 'tunnel')
		grid.set_cell((0, 6), 'rogue_door')
	def generate_appliances(self):
		self.enter_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
		enter_room = self.dungeon.grid.cell(self.enter_room_key)
		if self.depth == 0:
			yield (self.point_in_rect(enter_room), 'dungeon_enter')
		else:
			yield (self.point_in_rect(enter_room), 'enter', self.depth - 1)

		if not self.is_bottom:
			for _ in range(9):
				exit_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
				exit_room = self.dungeon.grid.cell(exit_room_key)
				if exit_room_key == self.enter_room_key:
					continue
			yield (self.point_in_rect(exit_room), 'exit', self.depth + 1)

	def generate_items(self):
		item_distribution = [
			(50, HealingPotion),
			(self.depth, Dagger),
			(self.depth // 2, Sword),
			(max(0, (self.depth-5) // 3), Axe),
			(self.depth, Rags),
			(self.depth // 2, Leather),
			(max(0, (self.depth-5) // 3), ChainMail),
			(max(0, (self.depth-10) // 3), PlateArmor),
			]
		item_distribution = [(_, (item_type.__name__,)) for (_, item_type) in item_distribution]
		for pos, item in self.distribute(builders.WeightedDistribution, item_distribution, self.amount_fixed(2, 4)
			):
			if item is None:
				continue
			room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
			room = self.dungeon.grid.cell(room_key)
			pos = self.point_in_rect(room)
			yield pos, item
		if self.is_bottom:
			for _ in range(9):
				exit_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
				exit_room = self.dungeon.grid.cell(exit_room_key)
				if exit_room_key == self.enter_room_key:
					continue
			yield (self.point_in_rect(exit_room), 'mcguffin')
	def generate_actors(self):
		monster_distribution = list(itertools.chain(
			easy_monsters.get_distribution(self.depth),
			norm_monsters.get_distribution(self.depth),
			hard_monsters.get_distribution(self.depth),
			))
		monster_distribution = [(_, (monster_type.__name__,)) for (_, monster_type) in monster_distribution]
		available_rooms = [room for room in self.dungeon.grid.keys() if room != self.enter_room_key]
		for pos, monster in self.distribute(builders.WeightedDistribution, monster_distribution,  self.amount_fixed(5)):
			if monster is None:
				continue
			room = self.dungeon.grid.cell(self.rng.choice(available_rooms))
			pos = self.point_in_rect(room)
			yield pos, monster

class RogueDungeonScene(Scene):
	MAX_LEVELS = 26
	SIZE = Size(78, 21)
	BUILDER = _Builder

class GameCompleted(Exception):
	pass

class RogueDungeon(src.engine.Game):
	def make_scene(self, scene_id):
		return RogueDungeonScene()
	def make_player(self):
		rogue = Rogue(None)
		rogue.grab(Dagger())
		return rogue

def main(ui):
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'oldrogue.sav')
	with clckwrkbdgr.serialize.stream.AutoSavefile(savefile) as savefile:
		dungeon = RogueDungeon()
		if savefile.reader:
			dungeon.load(savefile.reader)
		else:
			dungeon.generate(0)

		game = MainGame(dungeon)
		loop = clckwrkbdgr.tui.ModeLoop(ui)
		loop.run(game)
		if dungeon.is_finished():
			savefile.savefile.unlink()
		else:
			pass # savefile.save(dungeon, 666)

import click
@click.command()
@click.option('--debug', is_flag=True)
def cli(debug=False):
	clckwrkbdgr.logging.init('rogue',
			debug=debug,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	with clckwrkbdgr.tui.Curses() as ui:
		main(ui)

if __name__ == '__main__':
	cli()
