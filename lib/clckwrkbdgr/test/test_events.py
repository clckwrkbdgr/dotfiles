import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import os
from clckwrkbdgr.events import Events, MessageEvent

class TestEventChannel(unittest.TestCase):
	def _channel_name(self):
		import random
		return 'dotfiles_unittest_TestEventChannel_{0}'.format(random.random())
	def should_post_event_to_queue(self):
		channel_name = self._channel_name()
		Events(channel_name).trigger('test')
		self.assertEqual(Events(channel_name).pending(), 1)
		event = Events(channel_name).listen()
		self.assertEqual(event, 'test')
		self.assertEqual(Events(channel_name).pending(), 0)
	def should_detect_empty_queue(self):
		channel_name = self._channel_name()
		self.assertEqual(Events(channel_name).pending(), 0)
		event = Events(channel_name).listen()
		self.assertIsNone(event)

class TestMessageEvent(unittest.TestCase):
	def should_format_message_event(self):
		class MyMessage(MessageEvent):
			_message = 'Hello {who}!'
		event = MyMessage(who='world')
		self.assertEqual(str(event), 'Hello world!')
