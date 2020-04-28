import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import unittest.mock
unittest.mock.patch.TEST_PREFIX = 'should'
import os
import clckwrkbdgr.fs
from pathlib import Path

@unittest.mock.patch('os.getcwd', return_value='old')
@unittest.mock.patch('os.chdir')
class TestPathUtils(unittest.TestCase):
	def should_change_current_dir(self, mock_getcwd, mock_chdir):
		with clckwrkbdgr.fs.CurrentDir('new'):
			self.assertEqual(os.chdir.call_args, (('new',),))
		self.assertEqual(os.chdir.call_args, (('old',),))
	def should_use_path_object_to_change_current_dir(self, mock_getcwd, mock_chdir):
		with clckwrkbdgr.fs.CurrentDir(Path('new')):
			self.assertEqual(os.chdir.call_args, (('new',),))
		self.assertEqual(os.chdir.call_args, (('old',),))
