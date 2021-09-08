import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from clckwrkbdgr import tui
from clckwrkbdgr.tui import widgets

class TestKey(unittest.TestCase):
	def should_create_key(self):
		self.assertEqual(tui.Key(65).value, 65)
		self.assertEqual(tui.Key('A').value, 65)
		self.assertEqual(tui.Key(tui.Key('A')).value, 65)
	def should_compare_keys(self):
		self.assertTrue(tui.Key('A') == 65)
		self.assertTrue(65 == tui.Key('A'))
		self.assertTrue('A' == tui.Key('A'))
		self.assertTrue(tui.Key('A') == 'A')
		self.assertTrue(tui.Key('A') == tui.Key('A'))
		self.assertTrue(tui.Key('A') != 64)
		self.assertTrue(tui.Key('A') < 'B')
		self.assertTrue(tui.Key('A') <= 'A')
		self.assertTrue(tui.Key('A') > ' ')
		self.assertTrue(tui.Key('A') in ['A'])
		self.assertTrue(tui.Key('A') in {tui.Key('A')})

class TestUtils(unittest.TestCase):
	def should_fit_text_into_screen(self):
		lorem_ipsum = textwrap.dedent("""\
				Lorem ipsum dolor sit amet, consectetur adipiscing elit,
				sed do eiusmod tempor incididunt ut labore et dolore magna
				aliqua. Ut enim ad minim veniam, quis nostrud exercitation
				ullamco laboris nisi ut aliquip ex ea commodo consequat.
				Duis aute irure dolor in reprehenderit in voluptate velit
				esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
				occaecat cupidatat non proident, sunt in culpa qui officia
				deserunt mollit anim id est laborum.
				""")
		expected = [
				'Lorem ipsum dolor sit amet',
				'sed do eiusmod tempor inci',
				'aliqua. Ut enim ad minim v',
				'[...]',
				'esse cillum dolore eu fugi',
				'occaecat cupidatat non pro',
				'deserunt mollit anim id es',
			]
		self.assertEqual(tui.ExceptionScreen._fit_into_bounds(lorem_ipsum, len(expected[0]), len(expected)), expected)
		lorem_ipsum = textwrap.dedent("""\
				Lorem ipsum dolor sit amet, consectetur adipiscing elit,
				sed do eiusmod tempor incididunt ut labore et dolore magna
				aliqua. Ut enim ad minim veniam, quis nostrud exercitation
				ullamco laboris nisi ut aliquip ex ea commodo consequat.
				Duis aute irure dolor in reprehenderit in voluptate velit
				esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
				(CUT      to make odd number of lines)
				""")
		expected = [
				'Lorem ipsum dolor sit amet',
				'sed do eiusmod tempor inci',
				'[...]',
				'Duis aute irure dolor in r',
				'esse cillum dolore eu fugi',
				'(CUT      to make odd numb',
			]
		self.assertEqual(tui.ExceptionScreen._fit_into_bounds(lorem_ipsum, len(expected[0]), len(expected)), expected)
	def should_prepare_prompt_from_choices(self):
		self.assertEqual("", widgets.Prompt._prompt_from_choices([]))
		self.assertEqual("a", widgets.Prompt._prompt_from_choices(['a']))
		self.assertEqual("a-b", widgets.Prompt._prompt_from_choices(['a', 'b']))
		self.assertEqual("y,n", widgets.Prompt._prompt_from_choices(['y', 'n']))
		self.assertEqual("a-c", widgets.Prompt._prompt_from_choices(['a', 'b', 'c']))
		self.assertEqual("a-c,x-z", widgets.Prompt._prompt_from_choices(['a', 'b', 'c', 'x', 'y', 'z']))
		self.assertEqual("*,a-b", widgets.Prompt._prompt_from_choices(['a', 'b', '*']))
