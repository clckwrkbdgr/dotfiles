from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from .. import terrain
import clckwrkbdgr.serialize.stream as savefile

VERSION = 666

class Floor(terrain.Terrain):
	_sprite = '.'
	_name = 'floor'

class TestTerrainSavefile(unittest.TestCase):
	def should_load_terrain(self):
		stream = StringIO(str(VERSION) + '\x00Floor')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Terrain', {'Floor':Floor})
		cell = reader.read(terrain.Terrain)
		self.assertEqual(type(cell), Floor)
	def should_save_terrain(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		cell = Floor()
		writer.write(cell)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Floor')
