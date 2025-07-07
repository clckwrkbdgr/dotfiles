from .defs import *
from .engine import terrain

class Cell(terrain.Terrain):
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
