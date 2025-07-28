from clckwrkbdgr import unittest
from .. import events
from clckwrkbdgr import utils
from ..mock import *

class TestEvent(unittest.TestCase):
	def should_create_event_with_fields(self):
		event = DropItem('me', 'floor', what='something')
		self.assertEqual(repr(event), 'DropItem(who=me, where=floor, what=something)')
	def should_create_event_without_fields(self):
		event = NothingToDrop()
		self.assertEqual(repr(event), 'NothingToDrop()')

class TestEvents(unittest.TestCase):
	def should_handle_event_with_function_callback(self):
		event = DropItem('me', 'grass', 'something')
		callback = events.Events.get(event)
		self.assertEqual(callback(event), 'me drops something on grass')
	def should_handle_unknown_events(self):
		event = 'UNKNOWN EVENT'
		callback = events.Events.get(event)
		self.assertIsNone(callback)
	def should_handle_event_with_object_method(self):
		handler = Handler()
		message = events.Events.process(Hit('player', 'monster'), bind_self=handler)
		self.assertEqual(message, 'player -> monster')
