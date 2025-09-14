from src.engine.appliances import LevelPassage
from src.engine.ui import Sprite
from items import *

class StairsDown(LevelPassage):
	_sprite = Sprite('>', None)
	_name = 'stairs down'
	_id = 'exit'
	_can_go_down = True

class StairsUp(LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'stairs up'
	_id = 'enter'
	_can_go_up = True

class DungeonEntrance(LevelPassage):
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

class DungeonGates(LevelPassage):
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
