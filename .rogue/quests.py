from src.engine import actors
from src.engine.ui import Sprite

class Dweller(actors.Monster, actors.Neutral):
	_max_hp = 10
	_name = 'dweller'
	def __init__(self, pos, color=None):
		self._sprite = Sprite('@', color)
		super(Dweller, self).__init__(pos)
		self.quest = None
		self.prepared_quest = None
	def save(self, stream):
		super(Dweller, self).save(stream)
		stream.write(self._sprite.color)

		if self.quest:
			stream.write(self.quest[0])
			stream.write(self.quest[1])
			stream.write(self.quest[2])
		else:
			stream.write('')
		if self.prepared_quest:
			stream.write(self.prepared_quest[0])
			stream.write(self.prepared_quest[1])
			stream.write(self.prepared_quest[2])
		else:
			stream.write('')
	def load(self, stream):
		super(Dweller, self).load(stream)
		self._sprite = Sprite(self._sprite.sprite, stream.read())

		self.quest = stream.read()
		if self.quest:
			self.quest = (int(self.quest), stream.read(), stream.read(int))
		else:
			self.quest = None
		self.prepared_quest = stream.read()
		if self.prepared_quest:
			self.prepared_quest = (int(self.prepared_quest), stream.read(), stream.read(int))
		else:
			self.prepared_quest = None

