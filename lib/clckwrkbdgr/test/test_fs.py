import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
import os
import clckwrkbdgr.fs
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

@mock.patch('os.getcwd', return_value='old')
@mock.patch('os.chdir')
class TestPathUtils(unittest.TestCase):
	def should_change_current_dir(self, mock_getcwd, mock_chdir):
		with clckwrkbdgr.fs.CurrentDir('new'):
			self.assertEqual(os.chdir.call_args, (('new',),))
		self.assertEqual(os.chdir.call_args, (('old',),))
	def should_use_path_object_to_change_current_dir(self, mock_getcwd, mock_chdir):
		with clckwrkbdgr.fs.CurrentDir(Path('new')):
			self.assertEqual(os.chdir.call_args, (('new',),))
		self.assertEqual(os.chdir.call_args, (('old',),))
