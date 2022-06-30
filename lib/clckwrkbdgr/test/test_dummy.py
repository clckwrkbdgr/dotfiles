from clckwrkbdgr import unittest
import clckwrkbdgr.dummy as termcolor

class TestDummies(unittest.TestCase):
	def should_color_nothing(self):
		self.assertEqual(termcolor.colored('nothing'), 'nothing')
