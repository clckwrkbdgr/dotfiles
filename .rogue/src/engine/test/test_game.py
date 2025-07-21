from clckwrkbdgr import unittest
from .. import _base
from .. import events
from ..mock import *

class TestEvents(unittest.TestCase):
	def should_process_events(self):
		game = _base.Game()
		game.fire_event(MockEvent(who='me', where='here', what='something'))
		self.assertEqual(list(game.process_events()), [
			'me stands here wielding something',
			])
