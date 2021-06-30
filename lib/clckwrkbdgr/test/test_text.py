import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import pickle
from clckwrkbdgr.text import wrap_lines

class TestWrapping(unittest.TestCase):
	def should_wrap_text_lines_into_single_line(self):
		self.assertEqual(wrap_lines([], 5), (0, None))
		self.assertEqual(wrap_lines(["hello"], 5), (0, "hello"))
		self.assertEqual(wrap_lines(["hello", "world"], 5, ellipsis="!!!"), (-2, "he!!!"))
		self.assertEqual(wrap_lines(["hello world"], 8, ellipsis="!!!"), (-5, "hello!!!"))
		self.assertEqual(wrap_lines(["hello world", "second"], 8, ellipsis="!!!"), (-5, "hello!!!"))
		self.assertEqual(wrap_lines(["hello", "world"], 10, ellipsis="!!!"), (1, "hello!!!"))
		self.assertEqual(wrap_lines(["hello", "world"], 10, ellipsis="!!!", rjust_ellipsis=True), (1, "hello  !!!"))
		self.assertEqual(wrap_lines(["hello", "world"], 15, ellipsis="!!!"), (0, "hello world"))
		self.assertEqual(wrap_lines(["hello", "world", "second"], 15, sep='++', ellipsis="!!!"), (2, "hello++world!!!"))
		self.assertEqual(wrap_lines(["hello"], 5, ellipsis="!!!", force_ellipsis=True), (-2, "he!!!"))
		self.assertEqual(wrap_lines(["hello"], 10, ellipsis="!!!", force_ellipsis=True), (1, "hello!!!"))
