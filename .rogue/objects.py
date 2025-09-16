from clckwrkbdgr import utils
from src.engine import appliances
from src.engine.ui import Sprite
from items import *

class Door(appliances.Door):
	_opened_sprite = Sprite('-', 'white')
	_closed_sprite = Sprite('+', 'yellow')
	_name = 'door'

class LockedDoor(appliances.LockedDoor):
	pass

make_locked_door = MakeEntity(LockedDoor, '_unlocking_item _name _closed_sprite _opened_sprite')
make_locked_door('RedBlastDoor',   RedAccessCard,   'red blast door',   Sprite('+', 'red'), Sprite('-', 'white'))
make_locked_door('GreenBlastDoor', GreenAccessCard, 'green blast door', Sprite('+', 'green'), Sprite('-', 'white'))
make_locked_door('BlueBlastDoor',  BlueAccessCard,  'blue blast door',  Sprite('+', 'blue'), Sprite('-', 'white'))
make_locked_door('WoodenDoor',   BronzeKey,   'wooden door',  Sprite('+', 'yellow'), Sprite('-', 'white'))
make_locked_door('DeepDoor',     NavyKey,     'deep door',    Sprite('+', 'cyan'), Sprite('-', 'white'))
make_locked_door('FleshDoor',    FleshKey,    'flesh key',    Sprite('+', 'magenta'), Sprite('-', 'white'))
make_locked_door('SkeletonDoor', SkeletonKey, 'skeleton key', Sprite('+', 'white'), Sprite('-', 'white'))
make_locked_door('ObsidianDoor', ObsidianKey, 'obsidian key', Sprite('+', 'bold_black'), Sprite('-', 'white'))
make_locked_door('RubyDoor',     RubyKey,     'ruby key',     Sprite('+', 'bold_red'), Sprite('-', 'white'))
make_locked_door('EmeraldDoor',  EmeraldKey,  'emerald key',  Sprite('+', 'bold_green'), Sprite('-', 'white'))
make_locked_door('SaphireDoor',  SaphireKey,  'saphire key',  Sprite('+', 'bold_blue'), Sprite('-', 'white'))
make_locked_door('GoldenDoor',   GoldenKey,   'golden key',   Sprite('+', 'bold_yellow'), Sprite('-', 'white'))
make_locked_door('CrystalDoor',  CrystalKey,  'crystal key',  Sprite('+', 'bold_cyan'), Sprite('-', 'white'))
make_locked_door('InfernalDoor', InfernalKey, 'infernal key', Sprite('+', 'bold_magenta'), Sprite('-', 'white'))
make_locked_door('MarbleDoor',   MarbleKey,   'marble key',   Sprite('+', 'bold_white'), Sprite('-', 'white'))

class StairsDown(appliances.LevelPassage):
	_sprite = Sprite('>', None)
	_name = 'stairs down'
	_id = 'exit'
	_can_go_down = True

class StairsUp(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'stairs up'
	_id = 'enter'
	_can_go_up = True

class DungeonEntrance(appliances.LevelPassage):
	_sprite = Sprite('>', None)
	_name = 'dungeon entrance'
	_can_go_down = True
	def __init__(self, *args, **kwargs):
		entrance_id = kwargs.get('entrance_id')
		if 'entrance_id' in kwargs:
			del kwargs['entrance_id']
		super(DungeonEntrance, self).__init__(*args, **kwargs)
		self._id = entrance_id
	def load(self, stream):
		super(DungeonEntrance, self).load(stream)
		self._id = stream.read()
	def save(self, stream):
		super(DungeonEntrance, self).save(stream)
		stream.write(self._id)

class DungeonGates(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'exit from the dungeon'
	_id = 'enter'
	_can_go_up = True
	_unlocking_item = McGuffin

class ObjectMapping:
	@staticmethod
	def start():
		return 'start'
	@staticmethod
	def closed_door():
		return Door(True)
	@staticmethod
	def opened_door():
		return Door(False)
	@staticmethod
	def enter(prev_level_id):
		return StairsUp(prev_level_id, 'exit')
	@staticmethod
	def exit(next_level_id):
		return StairsDown(next_level_id, 'enter')
	@staticmethod
	def dungeon_entrance():
		return StairsDown('dungeon/0', 'enter')
	@staticmethod
	def rogue_dungeon_entrance(dungeon_id):
		return DungeonEntrance('rogue/{0}/0'.format(dungeon_id), 'enter', entrance_id='rogue/{0}'.format(dungeon_id))
	@staticmethod
	def rogue_dungeon_exit(full_dungeon_id):
		return DungeonGates('overworld', full_dungeon_id)
	@staticmethod
	def overworld_exit():
		return StairsUp('overworld', None)
	@staticmethod
	def locked_door(key_type):
		return next(_ for _ in utils.all_subclasses(LockedDoor) if _._closed_sprite.color == key_type)
