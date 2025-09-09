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

make_armor = MakeEntity((Item, Wearable), '_sprite _name _protection')
make_armor('Rags', Sprite("[", None), "rags", 1)
make_armor('Leather', Sprite("[", None), "leather", 2)
make_armor('ChainMail', Sprite("[", None), "chain mail", 3)
make_armor('PlateArmor', Sprite("[", None), "plate armor", 4)

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
