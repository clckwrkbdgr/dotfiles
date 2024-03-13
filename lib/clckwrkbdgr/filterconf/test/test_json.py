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

		"""
	def should_split_lines(self):
		content = 'foo\nbar\n'
		filter = PlainText(content)
		with filter.AutoSplitlines():
			self.assertEqual(filter.lines, ['foo', 'bar'])
			filter.lines[-1] = 'baz'
		self.assertEqual(filter.content, 'foo\nbaz\n')
	def should_split_lines_and_remember_trailing_newline(self):
		content = 'foo\nbar'
		filter = PlainText(content)
		with filter.AutoSplitlines():
			self.assertEqual(filter.lines, ['foo', 'bar'])
			filter.lines[-1] = 'baz'
		self.assertEqual(filter.content, 'foo\nbaz')
	def should_convert_pattern_by_type(self):
		regex = convert_pattern('[a-z]+', 'regex')
		self.assertTrue(regex.match('foo'))
		self.assertFalse(regex.match('123 foo'))
		self.assertTrue(regex.search('123 foo'))

		wildcard = convert_pattern('[a-z][a-z][a-z]', 'wildcard')
		self.assertTrue(wildcard.match('foo'))
		self.assertFalse(wildcard.match('123 foo'))
		self.assertTrue(wildcard.search('123 foo'))

		plain = convert_pattern('foo')
		self.assertTrue(plain.match('foo'))
		self.assertFalse(plain.match('123 foo'))
		self.assertTrue(plain.search('123 foo'))

	def should_sort_plain_text(self):
		content = '2\n3\n1\n'
		filter = PlainText(content)
		filter.sort()
		self.assertEqual(filter.content, '1\n2\n3\n')
	def should_delete_lines_by_pattern(self):
		content = 'foo\nbar\nbaz\n'
		filter = PlainText(content)
		filter.delete('ba.', pattern_type='regex')
		self.assertEqual(filter.content, 'foo\n')
	def should_regex_lines_by_pattern(self):
		content = 'foo\nbar\nbaz\n'
		filter = PlainText(content)
		filter.replace('ba(.)', r'woo\1', pattern_type='regex')
		self.assertEqual(filter.content, 'foo\nwoor\nwooz\n')
	def should_pretty_plain_text(self):
		content = 'foo\nbar\nbaz'
		filter = PlainText(content)
		filter.pretty()
		self.assertEqual(filter.content, 'foo\nbar\nbaz\n')
	"""
