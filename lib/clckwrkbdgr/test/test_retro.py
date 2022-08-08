import datetime
from .. import retro
from .. import unittest

class TestEntries(unittest.TestCase):
	def should_format_entry(self):
		entry = retro.Entry(datetime.datetime(2020, 12, 31, 8, 30), 'hello world')
		self.assertEqual(str(entry), '2020-12-31 08:30:00: hello world')
		self.assertEqual(repr(entry), "Entry(date=datetime.datetime(2020, 12, 31, 8, 30), title='hello world', details=<0 chars>)")

		entry = retro.Entry(datetime.datetime(2020, 12, 31, 8, 30), 'hello world', 'Lorem ipsum\ndolores sit amet')
		self.assertEqual(str(entry), '2020-12-31 08:30:00: hello world\n  Lorem ipsum\n  dolores sit amet')
		self.assertEqual(repr(entry), "Entry(date=datetime.datetime(2020, 12, 31, 8, 30), title='hello world', details=<28 chars>)")
	def should_order_entries(self):
		entries = [
				retro.Entry(datetime.datetime(2020, 12, 31, 10, 30), 'hello world', 'Lorem ipsum\ndolores sit amet'),
				retro.Entry(datetime.datetime(2020, 12, 31, 8, 30), 'hello world'),
				]
		self.assertEqual(sorted(entries), [
			entries[1],
			entries[0],
			])

		with self.assertRaises(TypeError):
			entries[0] < '<not an entry object>'
	def should_compare_entries(self):
		foo = retro.Entry(datetime.datetime(2020, 12, 31, 10, 30), 'hello world', 'Lorem ipsum\ndolores sit amet'),
		bar = retro.Entry(datetime.datetime(2020, 12, 31, 8, 30), 'hello world'),
		baz = retro.Entry(datetime.datetime(2020, 12, 31, 8, 30), 'hello world'),
		self.assertEqual(bar, baz)
		self.assertNotEqual(bar, foo)
		self.assertNotEqual(foo, baz)
		self.assertTrue(bar == baz)
		self.assertFalse(bar != baz)

class TestDateSearch(unittest.TestCase):
	def should_get_search_range(self):
		self.assertEqual(retro.get_search_range(now=datetime.datetime(2020, 12, 31, 8, 30)), (
			datetime.datetime(2020, 12, 31),
			datetime.datetime(2020, 12, 31, 23, 59, 59, 999999),
			))
		self.assertEqual(retro.get_search_range('20201230'), (
			datetime.datetime(2020, 12, 30),
			datetime.datetime(2020, 12, 30, 23, 59, 59, 999999),
			))
		self.assertEqual(retro.get_search_range('20201230083000', '20201231163000'), (
			datetime.datetime(2020, 12, 30, 8, 30),
			datetime.datetime(2020, 12, 31, 16, 30),
			))
