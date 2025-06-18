from clckwrkbdgr import unittest
from .. import events
from clckwrkbdgr import utils

class EmptyEvent(events.Event):
	FIELDS = ''
class MockEvent(events.Event):
	FIELDS = 'who where what'
class MockOtherEvent(events.Event):
	FIELDS = ('actor', 'target')

events.Events.on(EmptyEvent)(lambda event: '...')
events.Events.on(MockEvent)(lambda event: '{0} stands {1} wielding {2}'.format(event.who, event.where, event.what))
class Handler(object):
	@events.Events.on(MockOtherEvent)
	def handle_other_event(self, event):
		return '{0} -> {1}'.format(event.actor, event.target)

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
