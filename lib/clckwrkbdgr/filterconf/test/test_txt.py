from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.txt import PlainText

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

	def should_sort_plain_text(self):
		content = '2\n3\n1\n'
		filter = PlainText(content)
		filter.sort(None)
		self.assertEqual(filter.content, '1\n2\n3\n')
	def should_delete_lines_by_pattern(self):
		content = 'foo\nbar\nbaz\n'
		filter = PlainText(content)
		filter.delete(None, 'ba.', pattern_type='regex')
		self.assertEqual(filter.content, 'foo\n')
	def should_regex_lines_by_pattern(self):
		content = 'foo\nbar\nbaz\n'
		filter = PlainText(content)
		filter.replace(None, 'ba(.)', r'woo\1', pattern_type='regex')
		self.assertEqual(filter.content, 'foo\nwoor\nwooz\n')
	def should_pretty_plain_text(self):
		content = 'foo\nbar\nbaz'
		filter = PlainText(content)
		filter.pretty()
		self.assertEqual(filter.content, 'foo\nbar\nbaz\n')
