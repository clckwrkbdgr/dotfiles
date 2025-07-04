from clckwrkbdgr.utils import classfield

class Appliance(object):
	sprite = classfield('_sprite', '?')
	name = classfield('_name', 'unknown object')

class ObjectAtPos(object): # pragma: no cover -- TODO
	def __init__(self, pos, obj):
		self.pos = pos
		self.obj = obj
	def __repr__(self):
		return '{0} @{1}'.format(repr(self.obj), repr(self.pos))
	def __str__(self):
		return '{0} @{1}'.format(self.obj, self.pos)
	def __lt__(self, other):
		return (self.pos, self.obj) < (other.pos, other.obj)
	def __eq__(self, other):
		if isinstance(other, type(self)):
			return (self.pos, self.obj) == (other.pos, other.obj)
		return self.obj == other
	def __iter__(self):
		return iter((self.pos, self.obj))
	@classmethod
	def load(cls, reader):
		obj_class = reader.get_meta_info('ObjectClass')
		obj = reader.read(obj_class)
		pos = reader.read_point()
		return cls(pos, obj)
	def save(self, writer):
		writer.write(self.obj)
		writer.write(self.pos)
