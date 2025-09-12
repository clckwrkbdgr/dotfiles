from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from .. import quests
from ..mock import *

VERSION = 666

class TestSearialization(unittest.TestCase):
	def should_load_item(self):
		stream = StringIO(str(VERSION) + '\x00RandomQuest\x001\x00Ottilie Harsham')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Quests', {'RandomQuest':RandomQuest})
		quest = reader.read(quests.Quest)
		self.assertEqual(type(quest), RandomQuest)
		self.assertTrue(quest.is_active())
		self.assertEqual(quest.name, 'Ottilie Harsham')
	def should_save_item(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		quest = RandomQuest('Ottilie Harsham')
		writer.write(quest)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00RandomQuest\x000\x00Ottilie Harsham')

class TestQuests(unittest.TestCase):
	def should_create_inactive_quest(self):
		quest = RandomQuest()
		self.assertFalse(quest.is_active())
	def should_activatee_quest(self):
		quest = RandomQuest()
		quest.activate()
		self.assertTrue(quest.is_active())
