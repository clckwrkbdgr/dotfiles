from src.engine import actors
from src.engine.ui import Sprite
from src.engine.quests import Quest
from items import *

class ColoredSkinQuest(Quest):
	def __init__(self, required_amount=None, required_color=None, reward=None):
		super(ColoredSkinQuest, self).__init__()
		self.required_amount = required_amount
		self.required_color = required_color
		self.reward = reward
	def save(self, stream):
		super(ColoredSkinQuest, self).save(stream)
		stream.write(self.required_amount)
		stream.write(self.required_color)
		stream.write(self.reward)
	def load(self, stream):
		self.required_amount = stream.read_int()
		self.required_color = stream.read()
		self.reward = stream.read_int()
	
	def summary(self):
		return "Bring {0} {1}.".format(self.required_amount, self.required_color)
	def init_prompt(self):
		return 'Bring me {0} {1}, trade it for +{2} max hp, deal?'.format(self.required_amount, self.required_color, self.reward)
	def reminder(self):
		return 'Come back with {0} {1}.'.format(self.required_amount, self.required_color)
	def complete_prompt(self):
		return 'You have {0} {1}. Trade it for +{2} max hp?'.format(self.required_amount, self.required_color, self.reward)
	def _have_required_items(self, game):
		return list(
				game.scene.get_player().iter_items(ColoredSkin, name=self.required_color),
				)[:self.required_amount]
	def check(self, game):
		return len(self._have_required_items(game)) >= self.required_amount
	def complete(self, game):
		for item in self._have_required_items(game):
			game.scene.get_player().drop(item)
		if game.scene.get_player().hp == game.scene.get_player().max_hp:
			game.scene.get_player().hp += self.reward
		game.scene.get_player()._max_hp += self.reward

class Dweller(actors.Monster, actors.Neutral):
	_max_hp = 10
	_name = 'dweller'
	def __init__(self, pos, color=None):
		self._sprite = Sprite('@', color)
		super(Dweller, self).__init__(pos)
		self.quest = None
	def save(self, stream):
		super(Dweller, self).save(stream)
		stream.write(self._sprite.color)

		if self.quest:
			stream.write('.')
			self.quest.save(stream)
		else:
			stream.write('')
	def load(self, stream):
		super(Dweller, self).load(stream)
		self._sprite = Sprite(self._sprite.sprite, stream.read())

		self.quest = stream.read()
		if self.quest:
			self.quest = stream.read(Quest)
		else:
			self.quest = None

class QuestMapping:
	@staticmethod
	def dweller(pos, color):
		return Dweller(pos, color)
