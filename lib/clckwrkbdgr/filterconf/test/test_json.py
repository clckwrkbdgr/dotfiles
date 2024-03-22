import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.jsonfile import JSONConfig

class TestJSONConfig(unittest.TestCase):
	def should_sort_json(self):
		content = '{"foo":["value","1"],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"1",
						"value"
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(content) as filter:
			filter.sort("foo")
		self.assertEqual(filter.content, expected)
	def should_prettify_json(self):
		content = '{"foo":["value","1"],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						"1"
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(content) as filter:
			filter.pretty()
		self.assertEqual(filter.content, expected)
	def should_reindent_using_existing_indent(self):
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"1",
						"value"
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(expected) as filter:
			filter.sort("foo")
		self.assertEqual(filter.content, expected)
	def should_delete_keys_by_path(self):
		content = '{"foo":["value",1],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"foo": [
						"value",
						1
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("", "bar")
		self.assertEqual(filter.content, expected)

		content = '{"foo":["value",["sublist", 1]],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						[
							1
						]
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("foo.1", "sublist")
		self.assertEqual(filter.content, expected)
	def should_replace_values_by_path(self):
		content = '{"foo":["value",1],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "foobar",
					"foo": [
						"value",
						1
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.replace("bar", "baz", "foobar")
		self.assertEqual(filter.content, expected)

		content = '{"foo":["value",["sublist", 1]],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						[
							"fixed_sublist",
							1
						]
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.replace("foo.1.0", "sublist", "fixed_sublist")
		self.assertEqual(filter.content, expected)
