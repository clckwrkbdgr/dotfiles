from .defs import *
from .engine import terrain

class Terrain(object):
	""" Basic fixed stats shared by terrain cells of the same kind.
	- passable: allow free movement.
	- remembered: sprite for "remembered" state, where it is not seen directly, but was visited before.
	- allow_diagonal: allows diagonal movement to and from this cell. Otherwise only orthogonal movement is allowed.
	- dark: if True, no light is present and it is not considered transparent if further than 1 cell from the center.
	"""
	name = NotImplemented
	sprite = NotImplemented
	passable = True
	remembered = None
	allow_diagonal = True
	dark = False

class Cell(Terrain):
	""" Basic element for each terrain map. """
	def __init__(self, visited=False):
		self.terrain = self
		self.visited = visited
	@classmethod
	def load(cls, reader):
		terrain_type_name = reader.read()
		terrain_type = reader.get_meta_info('TERRAIN')[terrain_type_name]
		obj = terrain_type()
		obj.visited = reader.read_bool()
		return obj
	def save(self, writer):
		writer.write(type(self.terrain).__name__)
		writer.write(self.visited)
