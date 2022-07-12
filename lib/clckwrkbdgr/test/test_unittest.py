from .. import unittest
from .. import xdg

class TestCustomUnittest(unittest.TestCase):
	def should_recognize_prefix_should(self):
		self.assertTrue(True)
	def should_assert_count_equal_in_py2(self):
		self.assertCountEqual(
				['z', 1, 'a'],
				[1, 'a', 'z'],
				)
	def should_dedent(self):
		self.assertEqual(unittest.dedent("""\
				a
				b
				"""),
				"a\nb\n",
				)

class TestCustomFileSystemUnittest(unittest.fs.TestCase):
	MODULES = [xdg]
	def should_auto_setup_fake_fs(self):
		self.assertFalse(list(xdg.XDG_CONFIG_HOME.iterdir()))

