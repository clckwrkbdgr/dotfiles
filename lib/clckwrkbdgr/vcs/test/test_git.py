import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from pyfakefs import fake_filesystem_unittest

import clckwrkbdgr.vcs.git as git

class TestUtils(unittest.TestCase):
	def should_check_int_value(self):
		self.assertEqual(git.safe_int('1'), 1)
		self.assertEqual(git.safe_int('-1'), -1)
		self.assertEqual(git.safe_int('foo'), 'foo')

class TestGitWrapper(fake_filesystem_unittest.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[git])
	def should_detect_repo_root(self):
		self.fs.create_dir('/repo')
		self.fs.create_dir('/repo/.git')
		self.assertFalse(git.is_repo_root('/'))
		self.assertFalse(git.is_repo_root('/repo/'))
		self.assertFalse(git.is_repo_root('/repo/.git'))
		self.fs.create_file('/repo/.git/HEAD')
		self.assertTrue(git.is_repo_root('/repo/'))
