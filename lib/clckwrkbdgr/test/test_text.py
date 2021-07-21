import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import pickle
from clckwrkbdgr.text import wrap_lines
import clckwrkbdgr.text as text

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

class TestConversions(unittest.TestCase):
	def should_prettify_long_numbers(self):
		self.assertEqual(text.prettify_number(0), '0')
		self.assertEqual(text.prettify_number(666), '666')
		self.assertEqual(text.prettify_number(1000000), '1M')
		self.assertEqual(text.prettify_number(1234567), '1.23M')
	def should_convert_number_to_roman_repr(self):
		self.assertEqual(text.to_roman(6), 'VI')
		self.assertEqual(text.to_roman(76), 'LXXVI')
		self.assertEqual(text.to_roman(499), 'CDXCIX')
		self.assertEqual(text.to_roman(3888), 'MMMDCCCLXXXVIII')
	def should_convert_roman_repr_to_number(self):
		self.assertEqual(text.from_roman('VI'), 6)
		self.assertEqual(text.from_roman('LXXVI'), 76)
		self.assertEqual(text.from_roman('CDXCIX'), 499)
		self.assertEqual(text.from_roman('MMMDCCCLXXXVIII'), 3888)
	def should_convert_text_to_braille(self):
		self.assertEqual(text.to_braille("hello 1st World!"), (
			(1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1),
			(1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1),
			(0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0),
			(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
			(0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
			(0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0),
			(0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0))
			)
		self.assertEqual(text.to_braille("42"), (
			(0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0),
			(0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0),
			(1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0)))
		self.assertEqual(text.to_braille("CODE"), (
			(0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0),
			(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1),
			(0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0))
			)
		self.assertEqual(text.to_braille(u"0123456789"), (
			(0,1,0,0,1,0,0,1,0,1,0,0,0,1,0,1,0,0,0,1,0,1,1,0,0,1,0,1,1),
			(0,1,0,1,1,0,0,1,0,0,0,0,0,1,0,1,0,0,0,1,0,0,0,0,0,1,0,0,1),
			(1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0),
			(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
			(0,1,0,1,0,0,0,1,0,1,1,0,0,1,0,1,1,0,0,1,0,1,0,0,0,1,0,0,1),
			(0,1,0,0,1,0,0,1,0,1,0,0,0,1,0,1,1,0,0,1,0,1,1,0,0,1,0,1,0),
			(1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0))
			)
