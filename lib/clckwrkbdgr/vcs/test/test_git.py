from clckwrkbdgr import unittest

import clckwrkbdgr.vcs.git as git

class TestUtils(unittest.TestCase):
	def should_check_int_value(self):
		self.assertEqual(git.safe_int('1'), 1)
		self.assertEqual(git.safe_int('-1'), -1)
		self.assertEqual(git.safe_int('foo'), 'foo')

class TestGitWrapper(unittest.fs.TestCase):
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
