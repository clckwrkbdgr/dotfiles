import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from ..defs import Version
from .. import terrain
import clckwrkbdgr.serialize.stream as savefile
from . import mock_dungeon

class TestTerrainSavefile(unittest.TestCase):
	def should_load_terrain(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('TERRAIN', mock_dungeon.MockGame.TERRAIN)
		cell = reader.read(terrain.Cell)
		self.assertEqual(type(cell), mock_dungeon.MockGame.TERRAIN['name'])
		self.assertEqual(cell.visited, True)
	def should_save_terrain(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		cell = mock_dungeon.MockGame.TERRAIN['name']()
		cell.visited = True
		writer.write(cell)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00NameTerrain\x001')
