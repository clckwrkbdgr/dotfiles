import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from clckwrkbdgr.filterconf.txt import PlainText, convert_pattern

class TestPlainText(unittest.TestCase):
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
