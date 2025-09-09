import itertools
from src.engine.entity import MakeEntity, EntityClassDistribution
from src.engine import actors
from src.engine.ui import Sprite
from items import *

class Beast(actors.Monster):
	_hostile_to = [actors.Player]

class RealMonster(actors.EquippedMonster):
	_hostile_to = [actors.Player]

class Rogue(actors.EquippedMonster, actors.Player):
	_sprite = Sprite('@', 'bold_white')
	_name = 'rogue'
	_vision = 10
	_attack = 1
	_hostile_to = [Beast, RealMonster]
	init_max_hp = 10
	_max_inventory = 26
	def __init__(self, pos):
		self._max_hp = self.init_max_hp
		super(Rogue, self).__init__(pos)
		self.regeneration = 0
	def save(self, stream):
		super(Rogue, self).save(stream)
		stream.write(self.regeneration)
		stream.write(self.max_hp)
	def load(self, stream):
		super(Rogue, self).load(stream)
		self.regeneration = stream.read(int)
		self._max_hp = stream.read(int)
	def apply_auto_effects(self):
		if self.hp >= self.max_hp:
			return
		self.regeneration += 1
		while self.regeneration >= 10:
			self.regeneration -= 10
			self.affect_health(+1)
			if self.hp >= self.max_hp:
				self.hp = self.max_hp

class CarnivorousPlant(Beast, actors.Neutral):
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

class Slime(Beast, actors.Defensive):
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

class Rodent(Beast, actors.Offensive):
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

class BaseColoredMonster(Beast):
	_attack = 1
	_max_inventory = 1
	_hostile_to = [Rogue]
	_name = 'monster'
	def __init__(self, pos, sprite=None, max_hp=None):
		self._sprite = sprite
		self._max_hp = max_hp
		super(BaseColoredMonster, self).__init__(pos)
	@property
	def name(self):
		return self.sprite.color + ' ' + self._name
	def save(self, stream):
		super(BaseColoredMonster, self).save(stream)
		stream.write(self._sprite.sprite)
		stream.write(self._sprite.color)
		stream.write(self._max_hp)
	def load(self, stream):
		super(BaseColoredMonster, self).load(stream)
		self._sprite = Sprite(stream.read(), stream.read())
		self._max_hp = stream.read_int()

class ColoredMonster(BaseColoredMonster, actors.Defensive):
	pass

class AggressiveColoredMonster(BaseColoredMonster, actors.Offensive):
	_vision = 10

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

class MonsterMapping:
	@classmethod
	def colored_monster(cls, pos, sprite, color, strong, aggressive):
		monster_type = AggressiveColoredMonster if aggressive else ColoredMonster
		return monster_type(pos,
			Sprite(sprite.upper() if strong else sprite, color),
			1 + 10 * strong + random.randrange(4),
			)
	@classmethod
	def colored_monster_carrying(cls, pos, sprite, color, strong, aggressive):
		result = cls.colored_monster(pos, sprite, color, strong, aggressive)
		result.grab(ColoredSkin(
			Sprite('*', color),
			'{0} skin'.format(color.replace('_', ' ')),
			))
		return result
	@staticmethod
	def carnivorous_plant(pos,*data):
		return CarnivorousPlant(*(data + (pos,)))
	@staticmethod
	def slime(pos,*data):
		return Slime(*(data + (pos,)))
	@staticmethod
	def rodent(pos,*data):
		return Rodent(*(data + (pos,)))

for _monster_type in itertools.chain(easy_monsters, norm_monsters, hard_monsters):
	setattr(MonsterMapping, _monster_type.__name__, _monster_type)
