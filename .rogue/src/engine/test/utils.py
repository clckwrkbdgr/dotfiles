from clckwrkbdgr import unittest
from ..mock import *
from .. import _base

class MockWriterStream:
	def __init__(self):
		self.dump = []
	def write(self, item):
		if item == '\0':
			return
		self.dump.append(item)

class AbstractTestDungeon(unittest.TestCase):
	def _formatMessage(self, msg, standardMsg): # pragma: no cover
		if hasattr(self, 'dungeon'):
			msg = (msg or '') + '\n' + self.game.scene.tostring(self.game.scene.get_area_rect())
		return super(AbstractTestDungeon, self)._formatMessage(msg, standardMsg)
	def setUp(self):
		self.game = NanoDungeon()
		self.game.generate('floor')
		self.assertEqual([event for _, event in self.game.process_events(raw=True)], [_base.Events.Welcome()]) # Clear Welcome event.
