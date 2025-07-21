from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from .. import terrain
import clckwrkbdgr.serialize.stream as savefile
from ..mock import *

VERSION = 666

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
	def should_load_terrain_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00SoftFloor\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Terrain', {'SoftFloor':SoftFloor})
		cell = reader.read(terrain.Terrain)
		self.assertEqual(type(cell), SoftFloor)
		self.assertEqual(cell.softness, 1)
	def should_save_terrain_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		cell = SoftFloor(1)
		writer.write(cell)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00SoftFloor\x001')
