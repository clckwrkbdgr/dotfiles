import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
import os
import clckwrkbdgr.fs
try: # pragma: no cover
	import pathlib2 as pathlib
	from pathlib2 import Path
except ImportError: # pragma: no cover
	import pathlib
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

class TestFSUtils(unittest.TestCase):
	def should_create_valid_filename(self):
		self.assertEqual(clckwrkbdgr.fs.make_valid_filename('name/with/slashes'), 'name_with_slashes')
	@mock.patch(pathlib.__name__ + '.Path.exists', side_effect=(True, True, True, False))
	def should_create_unique_name(self, *mocks):
		self.assertEqual(clckwrkbdgr.fs.make_unique_filename('foo.bar'), Path('foo.2.bar'))
