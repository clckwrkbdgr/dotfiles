from clckwrkbdgr import unittest
from .. import events
from clckwrkbdgr import utils
from ..mock import *

class TestEvent(unittest.TestCase):
	def should_create_event_with_fields(self):
		event = MockEvent('me', 'here', what='something')
		self.assertEqual(repr(event), 'MockEvent(who=me, where=here, what=something)')
	def should_create_event_without_fields(self):
		event = EmptyEvent()
		self.assertEqual(repr(event), 'EmptyEvent()')

class TestEvents(unittest.TestCase):
	def should_handle_event_with_function_callback(self):
		event = MockEvent('me', 'here', 'something')
		callback = events.Events.get(event)
		self.assertEqual(callback(event), 'me stands here wielding something')
	def should_handle_event_with_object_method(self):
		handler = Handler()
		message = events.Events.process(MockOtherEvent('player', 'monster'), bind_self=handler)
		self.assertEqual(message, 'player -> monster')
