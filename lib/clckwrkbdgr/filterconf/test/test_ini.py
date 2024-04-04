import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.inifile import IniConfig

CONTENT = """[foo]
string = "Hello world"
boolean = true

[bar]
integer = 123456
"""

class TestIniConfig(unittest.TestCase):
	def should_prettify_ini_file(self):
		with IniConfig(CONTENT) as filter:
			filter.pretty()
		self.assertEqual(filter.content, CONTENT.lstrip() + '\n')
	def should_sort_keys_within_category(self):
		expected = unittest.dedent("""
			[foo]
			boolean = true
			string = "Hello world"

			[bar]
			integer = 123456

			""").lstrip()
		with IniConfig(CONTENT) as filter:
			filter.sort('foo')
		self.assertEqual(filter.content, expected)
	def should_sort_all_categories(self):
		expected = unittest.dedent("""
			[bar]
			integer = 123456

			[foo]
			boolean = true
			string = "Hello world"

			""").lstrip()
		with IniConfig(CONTENT) as filter:
			filter.sort('')
		self.assertEqual(filter.content, expected)
	def should_remove_keys(self):
		expected = unittest.dedent("""
			[foo]
			boolean = true

			[bar]

			""").lstrip()
		with IniConfig(CONTENT) as filter:
			filter.delete('foo/string', '*llo*', pattern_type='wildcard')
			filter.delete('bar/integer', '')
		self.assertEqual(filter.content, expected)
	def should_remove_categories(self):
		expected = unittest.dedent("""
			[bar]
			integer = 123456

			""").lstrip()
		with IniConfig(CONTENT) as filter:
			filter.delete('foo', '')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_in_nodes_by_specified_path_and_pattern(self):
		self.maxDiff = None
		expected = unittest.dedent("""
			[foo]
			string = "Herald"
			boolean = true

			[bar]
			integer = _____6

			""").lstrip()
		with IniConfig(CONTENT) as filter:
			filter.replace('foo/string', 'llo wor', 'ra')
			filter.replace('bar/integer', '[1-5]', '_', pattern_type='regex')
		self.assertEqual(filter.content, expected)
