import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from ..defs import Version
from .. import terrain
from ..system import savefile

class TestTerrainSavefile(unittest.TestCase):
	def setUp(self):
		self.TERRAIN = {
				'name' : terrain.Terrain('.', '.'),
				}
		self.TERRAIN['name'].name = 'name'
	def should_load_terrain(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('TERRAIN', self.TERRAIN)
		cell = reader.read(terrain.Cell)
		self.assertEqual(cell.terrain, self.TERRAIN['name'])
		self.assertEqual(cell.visited, True)
	def should_save_terrain(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		cell = terrain.Cell(self.TERRAIN['name'])
		cell.visited = True
		writer.write(cell)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00name\x001')
