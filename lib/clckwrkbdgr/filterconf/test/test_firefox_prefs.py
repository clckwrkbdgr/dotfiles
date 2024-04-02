import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.firefox_prefs import PrefsJSConfig

CONTENT = r"""
// Mozilla User Preferences

// Comment.

user_pref("boolean.value.true", true);
user_pref("integer.value", 123456);
user_pref("integer.other_value", 666);

user_pref("some_string.value", "foobar");
user_pref("boolean.value.false", false);
user_pref("value.with.escaped-quotes.inside", "{\"foo\":\"bar\"}");
"""

class TestPrefsJSConfig(unittest.TestCase):
	def should_prettify_prefs_js(self):
		with PrefsJSConfig(CONTENT) as filter:
			filter.pretty()
		self.assertEqual(filter.content, CONTENT)
	def should_sort_user_prefs_in_pref_js(self):
		expected = unittest.dedent(r"""
			// Mozilla User Preferences

			// Comment.

			user_pref("boolean.value.true", true);
			user_pref("integer.other_value", 666);
			user_pref("integer.value", 123456);

			user_pref("boolean.value.false", false);
			user_pref("some_string.value", "foobar");
			user_pref("value.with.escaped-quotes.inside", "{\"foo\":\"bar\"}");
			""")
		with PrefsJSConfig(CONTENT) as filter:
			filter.sort('')
		self.assertEqual(filter.content, expected)
	def should_remove_user_prefs_by_name(self):
		expected = unittest.dedent(r"""
			// Mozilla User Preferences

			// Comment.

			user_pref("integer.value", 123456);
			user_pref("integer.other_value", 666);

			user_pref("some_string.value", "foobar");
			user_pref("value.with.escaped-quotes.inside", "{\"foo\":\"bar\"}");
			""")
		with PrefsJSConfig(CONTENT) as filter:
			filter.delete('boolean.value.*', '')
		self.assertEqual(filter.content, expected)
	def should_remove_user_prefs_by_value(self):
		expected = unittest.dedent(r"""
			// Mozilla User Preferences

			// Comment.

			user_pref("boolean.value.true", true);
			user_pref("integer.value", 123456);
			user_pref("integer.other_value", 666);

			user_pref("boolean.value.false", false);
			user_pref("value.with.escaped-quotes.inside", "{\"foo\":\"bar\"}");
			""")
		with PrefsJSConfig(CONTENT) as filter:
			filter.delete('some_string.*', '*foo*', pattern_type='wildcard')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_in_nodes_by_specified_path_and_pattern(self):
		self.maxDiff = None
		expected = unittest.dedent(r"""
			// Mozilla User Preferences

			// Comment.

			user_pref("boolean.value.true", true);
			user_pref("integer.value", "foobar");
			user_pref("integer.other_value", 667);

			user_pref("some_string.value", "123456");
			user_pref("boolean.value.false", true);
			user_pref("value.with.escaped-quotes.inside", "{\"foo\":\"baz\"}");
			""")
		with PrefsJSConfig(CONTENT) as filter:
			filter.replace('integer.*value', '^1.*$', 'foobar', pattern_type='regex')
			filter.replace('integer.other_value', '666', '667', pattern_type='regex')
			filter.replace('some_string.*', '^.*$', '123456', pattern_type='regex')
			filter.replace('boolean.value.*', 'false', 'true', pattern_type='regex')
			filter.replace('value.*', 'bar', 'baz', pattern_type='regex')
		self.assertEqual(filter.content, expected)
