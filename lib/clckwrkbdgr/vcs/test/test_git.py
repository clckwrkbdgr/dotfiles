import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from pyfakefs import fake_filesystem_unittest

import clckwrkbdgr.vcs.git as git

class TestGitWrapper(fake_filesystem_unittest.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[git])
	def should_detect_repo_root(self):
		self.fs.create_dir('/repo')
		self.fs.create_dir('/repo/.git')
		self.assertFalse(git.is_repo_root('/'))
		self.assertTrue(git.is_repo_root('/repo/'))
		self.assertFalse(git.is_repo_root('/repo/.git'))
