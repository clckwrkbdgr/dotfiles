from .defs import *

class Terrain(object):
	""" Basic fixed stats shared by terrain cells of the same kind. """
	def __init__(self, name, sprite, passable=True, remembered=None, allow_diagonal=True, dark=False):
		""" Basic stats for terrain:
		- passable: allow free movement.
		- remembered: sprite for "remembered" state, where it is not seen directly, but was visited before.
		- allow_diagonal: allows diagonal movement to and from this cell. Otherwise only orthogonal movement is allowed.
		- dark: if True, no light is present and it is not considered transparent if further than 1 cell from the center.
		"""
		self.name = name
		self.sprite = sprite
		self.passable = passable
		self.remembered = remembered
		self.allow_diagonal = allow_diagonal
		self.dark = dark

class Cell(object):
	""" Basic element for each terrain map. """
	def __init__(self, terrain, visited=False):
		self.terrain = terrain
		self.visited = visited
	@classmethod
	def load(cls, reader):
		TERRAIN = reader.get_meta_info('TERRAIN')
		if reader.version > Version.TERRAIN_TYPES:
			obj = cls(TERRAIN[reader.read_str()])
			obj.visited = reader.read_bool()
		else:
			cell_type = reader.read_str(), reader.read_bool(), reader.read_str()
			for terrain in TERRAIN:
				if TERRAIN[terrain].sprite == cell_type[0] \
					and TERRAIN[terrain].passable == cell_type[1] \
					and TERRAIN[terrain].remembered == cell_type[2]:
					break
			obj = cls(TERRAIN[terrain])
			obj.visited = reader.read_bool()
		return obj
	def save(self, writer):
		writer.write(self.terrain.name)
		writer.write(self.visited)
