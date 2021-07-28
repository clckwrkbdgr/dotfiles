""" Very simple event system.

Events are organized using event channels (global, accessible by name).

Each event can essentially be any orbitrary object. It's up to sender/receiver how to process them.
"""
from collections import defaultdict
from clckwrkbdgr.utils import classfield

class MessageEvent(object):
	""" Simple text message with formatting.
	Each subclass should overrider field _message.
	Placeholders should be named and correspond to keyword args which are used to create new event.
	Formatted message is available via operator str().
	"""
	message = classfield('_message', '')
	def __init__(self, **kwargs):
		self.keywords = kwargs
	def __str__(self):
		return self.message.format(**(self.keywords))

class Events(object):
	""" Access to event channel by name. """
	_channels = defaultdict(list)
	def __init__(self, channel_name=None):
		""" Connects to the specified event channel.
		When name is not given, default (main) channel is connected.
		"""
		self.channel_name = channel_name or ''
		self.current = None
	def trigger(self, event):
		""" Adds new event to the channel. """
		self._channels[self.channel_name].append(event)
	def pending(self):
		""" Returns number of pending events. """
		return len(self._channels[self.channel_name])
	def listen(self):
		""" Pops and returns next event in channel queue.
		Also puts it into Events().current.
		Effectively reduces channel size.
		If there are no events left, returns None.
		"""
		if not self._channels[self.channel_name]:
			self.current = None
		else:
			self.current = self._channels[self.channel_name].pop(0)
		return self.current

