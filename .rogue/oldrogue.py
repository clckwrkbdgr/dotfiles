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
from src.engine.ui import Sprite

VERSION = 666

class MakeEntity:
	""" Creates builders for bare-properties-based classes to create subclass in one line. """
	def __init__(self, base_classes, *properties):
		""" Properties are either list of strings, or a single strings with space-separated identifiers. """
		self.base_classes = base_classes if clckwrkbdgr.utils.is_collection(base_classes) else (base_classes,)
		self.properties = properties
		if len(self.properties) == 1 and ' ' in self.properties[0]:
			self.properties = self.properties[0].split()
	def __call__(self, class_name, *values):
		""" Creates class object and puts it into global namespace.
		Values should match properties given at init.
		"""
		assert len(self.properties) == len(values), len(values)
		entity_class = type(class_name, self.base_classes, dict(zip(self.properties, values)))
		globals()[class_name] = entity_class
		return entity_class
class EntityClassDistribution:
	def __init__(self, prob):
		self.prob = prob
		self.classes = []
	def __lshift__(self, entity_class):
		self.classes.append(entity_class)
	def __iter__(self):
		return iter(self.classes)
	def get_distribution(self, param):
		if callable(self.prob):
			value = self.prob(param)
		else:
			value = self.prob
		return [(value, entity_class) for entity_class in self.classes]

class Void(src.engine.terrain.Terrain):
	_name = 'void'
	_sprite = Sprite(' ', None)
	_passable = False
class Corner(src.engine.terrain.Terrain):
	_name = 'corner'
	_sprite = Sprite("+", None)
	_passable = False
	_remembered = Sprite("+", None)
class RogueDoor(src.engine.terrain.Terrain):
	_name = 'rogue_door'
	_sprite = Sprite("+", None)
	_passable = True
	_remembered = Sprite("+", None)
	_allow_diagonal=False
	_dark=True
class Floor(src.engine.terrain.Terrain):
	_name = 'floor'
	_sprite = Sprite(".", None)
	_passable = True
class RoguePassage(src.engine.terrain.Terrain):
	_name = 'rogue_passage'
	_sprite = Sprite("#", None)
	_passable = True
	_remembered = Sprite("#", None)
	_allow_diagonal=False
	_dark=True
class WallH(src.engine.terrain.Terrain):
	_name = 'wall_h'
	_sprite = Sprite("-", None)
	_passable = False
	_remembered = Sprite("-", None)
class WallV(src.engine.terrain.Terrain):
	_name = 'wall_v'
	_sprite = Sprite("|", None)
	_passable = False
	_remembered = Sprite("|", None)

class StairsUp(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'stairs up'
	_id = 'enter'
	_can_go_up = True

class McGuffin(Item):
	_sprite = Sprite("*", None)
	_name = "mcguffin"

class DungeonGates(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'exit from the dungeon'
	_id = 'enter'
	_can_go_up = True
	_unlocking_item = McGuffin
	def use(self, who):
		if super().use(who):
			raise GameCompleted()

class StairsDown(appliances.LevelPassage):
	_sprite = Sprite('>', None)
	_name = 'stairs down'
	_id = 'exit'
	_can_go_down = True

class HealingPotion(Item, Consumable):
	_sprite = Sprite("!", None)
	_name = "potion"
	def consume(self, who):
		who.affect_health(10)
		return [DrinksHealingPotion(Who=who.name.title())]

make_weapon = MakeEntity(Item, '_sprite _name _attack')
make_weapon('Dagger', Sprite('(', None), 'dagger', 1)
make_weapon('Sword', Sprite('(', None), 'sword', 2)
make_weapon('Axe', Sprite('(', None), 'axe', 4)

make_armor = MakeEntity((Item, Wearable), '_sprite _name _protection')
make_armor('Rags', Sprite("[", None), "rags", 1)
make_armor('Leather', Sprite("[", None), "leather", 2)
make_armor('ChainMail', Sprite("[", None), "chain mail", 3)
make_armor('PlateArmor', Sprite("[", None), "plate armor", 4)

class RealMonster(actors.EquippedMonster, actors.Offensive):
	_hostile_to = [actors.Player]

class Rogue(actors.EquippedMonster, actors.Player):
	_hostile_to = [RealMonster]
	_sprite = Sprite("@", None)
	_name = "rogue"
	_max_hp = 25
	_attack = 1
	_max_inventory = 26

animal_drops = [
			(70, None),
			(20, HealingPotion),
			(5, Dagger),
			(5, Rags),
			]
monster_drops = [
			(78, None),
			(3, HealingPotion),
			(3, Dagger),
			(3, Sword),
			(3, Axe),
			(3, Rags),
			(3, Leather),
			(3, ChainMail),
			(1, PlateArmor),
		]
thug_drops = [
			(10, None),
			(20, HealingPotion),
			(30, Dagger),
			(10, Sword),
			(30, Leather),
			]
warrior_drops = [
			(40, None),
			(30, HealingPotion),
			(10, Dagger),
			(5, Sword),
			(10, Leather),
			(5, ChainMail),
			]
super_warrior_drops = [
			(80, None),
			(5, HealingPotion),
			(5, Axe),
			(10, Leather),
			]
easy_monsters = EntityClassDistribution(1)
norm_monsters = EntityClassDistribution(lambda depth: max(0, (depth-2)))
hard_monsters = EntityClassDistribution(lambda depth: max(0, (depth-7)//2))
make_monster = MakeEntity((RealMonster), '_sprite _name _max_hp _attack _drops')
easy_monsters << make_monster('Ant', Sprite('a', None), 'ant', 5, 1, animal_drops)
easy_monsters << make_monster('Bat', Sprite('b', None), 'bat', 5, 1, animal_drops)
easy_monsters << make_monster('Cockroach', Sprite('c', None), 'cockroach', 5, 1, animal_drops)
easy_monsters << make_monster('Dog', Sprite('d', None), 'dog', 7, 1, animal_drops)
norm_monsters << make_monster('Elf', Sprite('e', None), 'elf', 10, 2, warrior_drops)
easy_monsters << make_monster('Frog', Sprite('f', None), 'frog', 5, 1, animal_drops)
norm_monsters << make_monster('Goblin', Sprite("g", None), "goblin", 10, 2, warrior_drops*2)
norm_monsters << make_monster('Harpy', Sprite('h', None), 'harpy', 10, 2, monster_drops)
norm_monsters << make_monster('Imp', Sprite('i', None), 'imp', 10, 3, monster_drops)
easy_monsters << make_monster('Jelly', Sprite('j', None), 'jelly', 5, 2, animal_drops)
norm_monsters << make_monster('Kobold', Sprite('k', None), 'kobold', 10, 2, warrior_drops)
easy_monsters << make_monster('Lizard', Sprite('l', None), 'lizard', 5, 1, animal_drops)
easy_monsters << make_monster('Mummy', Sprite('m', None), 'mummy', 10, 2, monster_drops)
norm_monsters << make_monster('Narc', Sprite('n', None), 'narc', 10, 2, thug_drops)
norm_monsters << make_monster('Orc', Sprite('o', None), 'orc', 15, 3, warrior_drops*2)
easy_monsters << make_monster('Pigrat', Sprite('p', None), 'pigrat', 10, 2, animal_drops)
easy_monsters << make_monster('Quokka', Sprite('q', None), 'quokka', 5, 1, animal_drops)
easy_monsters << make_monster('Rat', Sprite("r", None), "rat", 5, 1, animal_drops)
norm_monsters << make_monster('Skeleton', Sprite('s', None), 'skeleton', 20, 2, monster_drops)
norm_monsters << make_monster('Thug', Sprite('t', None), 'thug', 15, 3, thug_drops*2)
norm_monsters << make_monster('Unicorn', Sprite('u', None), 'unicorn', 15, 3, monster_drops)
norm_monsters << make_monster('Vampire', Sprite('v', None), 'vampire', 20, 2, monster_drops)
easy_monsters << make_monster('Worm', Sprite('w', None), 'worm', 5, 2, animal_drops)
hard_monsters << make_monster('Exterminator', Sprite('x', None), 'exterminator', 20, 3, super_warrior_drops)
norm_monsters << make_monster('Yak', Sprite('y', None), 'yak', 10, 2, animal_drops)
easy_monsters << make_monster('Zombie', Sprite('z', None), 'zombie', 5, 2, thug_drops)
hard_monsters << make_monster('Angel', Sprite('A', None), 'angel', 30, 5, super_warrior_drops)
norm_monsters << make_monster('Beholder', Sprite('B', None), 'beholder', 20, 2, warrior_drops)
hard_monsters << make_monster('Cyborg', Sprite('C', None), 'cyborg', 20, 5, super_warrior_drops*3)
hard_monsters << make_monster('Dragon', Sprite('D', None), 'dragon', 40, 5, monster_drops*3)
norm_monsters << make_monster('Elemental', Sprite('E', None), 'elemental', 10, 2, [])
hard_monsters << make_monster('Floater', Sprite('F', None), 'floater', 40, 1, animal_drops)
hard_monsters << make_monster('Gargoyle', Sprite('G', None), 'gargoyle', 30, 3, monster_drops)
hard_monsters << make_monster('Hydra', Sprite('H', None), 'hydra', 30, 2, monster_drops)
norm_monsters << make_monster('Ichthyander', Sprite('I', None), 'ichthyander', 20, 2, thug_drops)
hard_monsters << make_monster('Juggernaut', Sprite('J', None), 'juggernaut', 40, 4, monster_drops)
hard_monsters << make_monster('Kraken', Sprite('K', None), 'kraken', 30, 3, monster_drops)
norm_monsters << make_monster('Lich', Sprite('L', None), 'lich', 20, 2, monster_drops)
norm_monsters << make_monster('Minotaur', Sprite('M', None), 'minotaur', 20, 2, warrior_drops*2)
norm_monsters << make_monster('Necromancer', Sprite('N', None), 'necromancer', 20, 2, warrior_drops)
hard_monsters << make_monster('Ogre', Sprite('O', None), 'ogre', 30, 5, super_warrior_drops)
hard_monsters << make_monster('Phoenix', Sprite('P', None), 'phoenix', 20, 3, monster_drops)
norm_monsters << make_monster('QueenBee', Sprite('Q', None), 'queen bee', 20, 2, animal_drops)
hard_monsters << make_monster('Revenant', Sprite('R', None), 'revenant', 20, 3, super_warrior_drops)
norm_monsters << make_monster('Snake', Sprite('S', None), 'snake', 10, 2, animal_drops)
hard_monsters << make_monster('Troll', Sprite("T", None), "troll", 25, 5, super_warrior_drops)
norm_monsters << make_monster('Unseen', Sprite('U', None), 'unseen', 10, 2, thug_drops)
norm_monsters << make_monster('Viper', Sprite('V', None), 'viper', 10, 2, animal_drops)
hard_monsters << make_monster('Wizard', Sprite('W', None), 'wizard', 40, 5, thug_drops*2)
hard_monsters << make_monster('Xenomorph', Sprite('X', None), 'xenomorph', 30, 3, animal_drops)
norm_monsters << make_monster('Yeti', Sprite('Y', None), 'yeti', 10, 2, animal_drops)
norm_monsters << make_monster('Zealot', Sprite('Z', None), 'zealot', 10, 2, thug_drops)

events.Events.on(Events.GodModeSwitched)(lambda event:"God {name} -> {state}".format(name=event.name, state=event.state))

events.Events.on(Events.NeedKey)(lambda event:"You cannot escape the dungeon without {0}!".format(event.key))
events.Events.on(Events.Ascend)(lambda event:"Going up...")
events.Events.on(Events.Descend)(lambda event:"Going down...")
events.Events.on(Events.CannotDescend)(lambda event:"Cannot dig through the ground.")
events.Events.on(Events.CannotAscend)(lambda event:"Cannot reach the ceiling.")

events.Events.on(Events.InventoryIsFull)(lambda event: "Inventory is full! Cannot pick up {item}".format(item=event.item.name))
events.Events.on(Events.GrabItem)(lambda event: "Grabbed {item}.".format(who=event.actor.name, item=event.item.name))
events.Events.on(Events.NothingToPickUp)(lambda event:"There is nothing here to pick up.")
events.Events.on(Events.InventoryIsEmpty)(lambda event:"Inventory is empty.")
events.Events.on(Events.DropItem)(lambda event:"{Who} drops {item}.".format(Who=event.who.name.title(), item=event.item.name))

events.Events.on(Events.NotConsumable)(lambda event:"Cannot consume {item}.".format(item=event.item.name))
events.Events.on(Events.ConsumeItem)(lambda event:"Consumed {item}.".format(item=event.item.name))
class DrinksHealingPotion(events.Event): FIELDS = 'Who'
events.Events.on(DrinksHealingPotion)(lambda event:"{Who} heals itself.".format(Who=event.Who))

events.Events.on(Events.NotWielding)(lambda event:"Nothing is wielded already.")
events.Events.on(Events.Unwield)(lambda event:"Unwielding {item}.".format(item=event.item.name))
events.Events.on(Events.Wield)(lambda event:"Wielding {item}.".format(item=event.item.name))

events.Events.on(Events.NotWearable)(lambda event:"Cannot wear {item}.".format(item=event.item.name))
events.Events.on(Events.NotWearing)(lambda event:"Nothing is worn already.")
events.Events.on(Events.TakeOff)(lambda event:"Taking off {item}.".format(item=event.item.name))
events.Events.on(Events.Wear)(lambda event:"Wearing {item}.".format(item=event.item.name))

events.Events.on(Events.Attack)(lambda event: "{Who} hit {whom} for {damage} hp.".format(Who=event.who.name.title(), whom=event.whom.name, damage=event.damage))
events.Events.on(Events.Death)(lambda event:"{Who} is dead.".format(Who=event.who.name.title()))
@events.Events.on(Events.BumpIntoTerrain)
def bumps_into_terrain(event):
	if not isinstance(event.actor, actors.Player):
		return "{Who} bumps into wall.".format(Who=event.actor.name.title())
events.Events.on(Events.BumpIntoActor)(lambda event:"{Who} bumps into {whom}.".format(Who=event.who.name.title(), whom=event.whom.name))

events.Events.on(Events.WelcomeBack)(lambda event:"Welcome back, {who}!".format(who=event.who.name))

class _Builder(builders.Builder):
	class Mapping:
		HealingPotion = HealingPotion
		corner = Corner()
		floor = Floor()
		tunnel = RoguePassage()
		door = RogueDoor()
		wall_h = WallH()
		wall_v = WallV()
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
		grid.set_cell((0, 6), 'door')
	def generate_appliances(self):
		self.enter_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
		enter_room = self.dungeon.grid.cell(self.enter_room_key)
		yield (self.point_in_rect(enter_room), 'enter')

		if not self.is_bottom:
			for _ in range(9):
				exit_room_key = self.rng.choice(list(self.dungeon.grid.size.iter_points()))
				exit_room = self.dungeon.grid.cell(exit_room_key)
				if exit_room_key == self.enter_room_key:
					continue
			yield (self.point_in_rect(exit_room), 'exit')

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
			yield (self.point_in_rect(exit_room), 'exit_item')
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

class RogueDungeonGenerator(object):
	MAX_LEVELS = 26
	SIZE = Size(78, 21)
	def build_level(self, scene, level_id):
		if level_id < 0 or level_id >= self.MAX_LEVELS:
			raise KeyError("Invalid level ID: {0} (supports only [0; {1}))".format(level_id, self.MAX_LEVELS))
		depth = level_id
		is_bottom = depth >= (self.MAX_LEVELS - 1)

		enter_object_type = StairsUp if level_id > 0 else DungeonGates
		prev_level_id = level_id - 1 if level_id > 0 else None
		next_level_id = level_id + 1 if not is_bottom else None
		builder = _Builder(depth, is_bottom, RNG(), self.SIZE)
		builder.map_key(enter=lambda:enter_object_type(prev_level_id, 'exit'))
		if is_bottom:
			builder.map_key(exit_item=lambda:McGuffin())
		else:
			builder.map_key(exit=lambda:StairsDown(next_level_id, 'enter'))
		monster_distribution = list(itertools.chain(
			easy_monsters.get_distribution(depth),
			norm_monsters.get_distribution(depth),
			hard_monsters.get_distribution(depth),
			))
		for _, monster_type in monster_distribution:
			builder.map_key(**{monster_type.__name__:monster_type})
		builder.map_key(**{'void':Void()})
		builder.generate()
		scene.size = self.SIZE
		scene.rooms = builder.dungeon.grid
		scene.tunnels = builder.dungeon.tunnels
		scene.terrain = builder.make_grid()
		scene.objects = list(builder.make_appliances())
		scene.items = list(builder.make_items())
		scene.monsters = list(builder.make_actors())
		#monster = monster()
		#monster.fill_drops(self.rng)

class GameCompleted(Exception):
	pass

class MainGame(ui.MainGame):
	INDICATORS = [
			ui.Indicator((0, 24), 9, lambda dungeon: 'Depth: ' + str(1+dungeon.game.current_scene_id)),
			ui.Indicator((10, 24), 10, lambda dungeon: "HP: " + "{0}/{1}".format(dungeon.game.scene.get_player().hp, dungeon.game.scene.get_player().max_hp)),
			ui.Indicator((21, 24), 9, lambda dungeon:"Items: " + (
				'' if not dungeon.game.scene.get_player().inventory else (
					''.join(item.sprite.sprite for item in dungeon.game.scene.get_player().inventory)
					if len(dungeon.game.scene.get_player().inventory) <= 2
					else len(dungeon.game.scene.get_player().inventory)
					))),
			ui.Indicator((31, 24), 12, lambda dungeon: "Wld: " + (dungeon.game.scene.get_player().wielding.name if dungeon.game.scene.get_player().wielding else '')),
			ui.Indicator((44, 24), 13, lambda dungeon: "Wear: " + (dungeon.game.scene.get_player().wearing.name if dungeon.game.scene.get_player().wearing else '')),
			ui.Indicator((58, 24), 7, lambda dungeon: "Here: " + dungeon.sprite_here(dungeon.game.scene.get_player().pos)),
			]
	def sprite_here(self, pos):
		item = next(self.game.scene.iter_items_at(pos), None)
		if item:
			return item.sprite.sprite
		obj = next(self.game.scene.iter_appliances_at(pos), None)
		if obj:
			return obj.sprite.sprite
		return ''
	def get_viewrect(self):
		return self.game.scene.get_area_rect()
	def get_map_shift(self):
		return Point(0, 1)
	def get_message_line_rect(self):
		return Rect(Point(0, 0), Size(80, 1))

class RogueDungeon(src.engine.Game):
	def make_scene(self, scene_id):
		return Scene(RogueDungeonGenerator())
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
