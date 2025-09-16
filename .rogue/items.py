from src.engine.items import Item, Consumable, Wearable
from src.engine.ui import Sprite
from src.engine import Events
from src.engine.entity import MakeEntity

class Healing(Consumable):
	healing = 0
	def consume(self, target):
		diff = target.affect_health(self.healing)
		return [Events.Health(target, diff)]

class HealingPotion(Item, Healing):
	_sprite = Sprite('!', None)
	_name = 'healing potion'
	healing = +5

class McGuffin(Item):
	_sprite = Sprite("*", None)
	_name = "mcguffin"

class ColoredSkin(Item):
	def __init__(self, sprite=None, name=None):
		self._sprite = sprite
		self._name = name
	def save(self, stream):
		super(ColoredSkin, self).save(stream)
		stream.write(self._sprite.sprite)
		stream.write(self._sprite.color)
		stream.write(self._name)
	def load(self, stream):
		self._sprite = Sprite(stream.read(), stream.read())
		self._name = stream.read()

make_weapon = MakeEntity(Item, '_sprite _name _attack')
make_weapon('Dagger', Sprite('(', None), 'dagger', 1)
make_weapon('Sword', Sprite('(', None), 'sword', 2)
make_weapon('Axe', Sprite('(', None), 'axe', 4)

make_armor = MakeEntity((Item, Wearable), '_sprite _name _protection _speed_penalty')
make_armor('Rags', Sprite("[", None), "rags", 1, 1.0)
make_armor('Leather', Sprite("[", None), "leather", 2, 1.0)
make_armor('ChainMail', Sprite("[", None), "chain mail", 3, 1.5)
make_armor('PlateArmor', Sprite("[", None), "plate armor", 4, 2.0)

class DoorKey(Item):
	pass

make_key = MakeEntity(DoorKey, '_name _sprite')
make_key('RedAccessCard',   'red access card',   Sprite('*', 'red'))
make_key('GreenAccessCard', 'green access card', Sprite('*', 'green'))
make_key('BlueAccessCard',  'blue access card',  Sprite('*', 'blue'))
make_key('BronzeKey',   'bronze key',   Sprite('*', 'yellow'))
make_key('NavyKey',     'navy key',     Sprite('*', 'cyan'))
make_key('FleshKey',    'flesh key',    Sprite('*', 'magenta'))
make_key('SkeletonKey', 'skeleton key', Sprite('*', 'white'))
make_key('ObsidianKey', 'obsidian key', Sprite('*', 'bold_black'))
make_key('RubyKey',     'ruby key',     Sprite('*', 'bold_red'))
make_key('EmeraldKey',  'emerald key',  Sprite('*', 'bold_green'))
make_key('SaphireKey',  'saphire key',  Sprite('*', 'bold_blue'))
make_key('GoldenKey',   'golden key',   Sprite('*', 'bold_yellow'))
make_key('CrystalKey',  'crystal key',  Sprite('*', 'bold_cyan'))
make_key('InfernalKey', 'infernal key', Sprite('*', 'bold_magenta'))
make_key('MarbleKey',   'marble key',   Sprite('*', 'bold_white'))

class ItemMapping:
	HealingPotion = HealingPotion
	mcguffin = McGuffin
	Dagger = Dagger
	Sword = Sword
	Axe = Axe
	Rags = Rags
	Leather = Leather
	ChainMail = ChainMail
	PlateArmor = PlateArmor
	@staticmethod
	def door_key(key_type):
		return next(_ for _ in utils.all_subclasses(DoorKey) if _._sprite.color == key_type)
