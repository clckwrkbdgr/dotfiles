class Item(object):
	pass

class ItemAtPos(object):
	def __init__(self, pos, item):
		self.pos = pos
		self.item = item
	def __str__(self):
		return '{0} @{1}'.format(self.item, self.pos)
	def __eq__(self, item):
		return self.item == item
	def __iter__(self):
		return iter((self.pos, self.item))
	@classmethod
	def load(cls, reader):
		item_class = reader.get_meta_info('ItemClass')
		item = reader.read(item_class)
		pos = reader.read_point()
		return cls(pos, item)
	def save(self, writer):
		writer.write(self.item)
		writer.write(self.pos)
