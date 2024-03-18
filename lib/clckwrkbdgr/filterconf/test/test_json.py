import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.jsonfile import JSONConfig

class TestJSONConfig(unittest.TestCase):
	def should_sort_and_prettify_json(self):
		content = '{"foo":["value",1],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						1
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		filter = JSONConfig(content)
		filter.sort()
		self.assertEqual(filter.content, expected)

		filter = JSONConfig(content)
		filter.pretty()
		self.assertEqual(filter.content, expected)
	def should_reindent_using_existing_indent(self):
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						1
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		filter = JSONConfig(expected)
		filter.sort()
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

		filter = JSONConfig(content)
		filter.delete("bar")
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

		filter = JSONConfig(content)
		filter.delete("foo.1.0")
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

		filter = JSONConfig(content)
		filter.replace("bar", "foobar")
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

		filter = JSONConfig(content)
		filter.replace("foo.1.0", "fixed_sublist")
		self.assertEqual(filter.content, expected)
