from clckwrkbdgr import unittest
from .. import _base
from .. import events

class MockEvent(events.Event):
	FIELDS = 'what'

events.Events.on(MockEvent)(lambda event: '{0} happened.'.format(event.what.title()))

class TestEvents(unittest.TestCase):
	def should_process_events(self):
		game = _base.Game()
		game.fire_event(MockEvent(what='something'))
		self.assertEqual(list(game.process_events()), [
			'Something happened.',
			])
