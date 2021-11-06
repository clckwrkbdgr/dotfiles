import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from pyfakefs import fake_filesystem_unittest

import os
from clckwrkbdgr import xdg
import clckwrkbdgr.taskwarrior
import clckwrkbdgr.taskwarrior._base
from clckwrkbdgr.taskwarrior import TaskWarrior

class TestTaskWarrior(fake_filesystem_unittest.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[clckwrkbdgr.taskwarrior, clckwrkbdgr.taskwarrior._base])
		taskwarrior_dir = xdg.save_data_path('taskwarrior')
		if not taskwarrior_dir.exists():
			self.fs.create_dir(str(taskwarrior_dir))
	def should_return_current_task(self):
		task = TaskWarrior()
		self.assertIsNone(task.get_current_task())
		task.start('foo')
		self.assertEqual(task.get_current_task(), 'foo')
		task.start('bar')
		self.assertEqual(task.get_current_task(), 'bar')
		task.stop()
		self.assertIsNone(task.get_current_task())
	def should_start_task(self):
		task = TaskWarrior()
		self.assertIsNone(task.get_current_task())
		task.start('foo')
		self.assertEqual(task.get_current_task(), 'foo')
	def should_stop_task(self):
		task = TaskWarrior()
		self.assertIsNone(task.get_current_task())
		task.start('foo')
		self.assertEqual(task.get_current_task(), 'foo')
		task.stop()
		self.assertIsNone(task.get_current_task())
	def should_resume_stopped_task(self):
		task = TaskWarrior()
		self.assertFalse(task.start())
		self.assertIsNone(task.get_current_task())

		task.start('foo')
		task.stop()
		self.assertTrue(task.start())
		self.assertEqual(task.get_current_task(), 'foo')
	def should_list_task_history(self):
		task = TaskWarrior()
		task.start('foo')
		task.start('bar')
		task.stop()
		self.assertEqual([_.title for _ in task.get_history()], ['foo', 'bar', None])
	@mock.patch('subprocess.call', side_effect=[0])
	def should_fix_task_history(self, subprocess_call):
		task = TaskWarrior()
		self.assertTrue(task.fix_history())
		subprocess_call.assert_has_calls([
			mock.call([os.environ.get('EDITOR', 'vi'), str(task._taskfile)]),
			])
