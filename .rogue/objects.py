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

class DungeonGates(LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'exit from the dungeon'
	_id = 'enter'
	_can_go_up = True
	_unlocking_item = McGuffin
	def use(self, who):
		if super().use(who):
			raise GameCompleted()

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
	dungeon_enter = lambda:DungeonGates(None, 'exit')
