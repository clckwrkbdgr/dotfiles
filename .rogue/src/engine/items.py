from clckwrkbdgr.utils import classfield

class Item(object):
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown item')

class ItemAtPos(object): # pragma: no cover -- TODO
	def __init__(self, pos, item):
		self.pos = pos
		self.item = item
	def __repr__(self):
		return '{0} @{1}'.format(repr(self.item), repr(self.pos))
	def __str__(self):
		return '{0} @{1}'.format(self.item, self.pos)
	def __lt__(self, other):
		return (self.pos, self.item) < (other.pos, other.item)
	def __eq__(self, other):
		if isinstance(other, type(self)):
			return (self.pos, self.item) == (other.pos, other.item)
		return self.item == other
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
