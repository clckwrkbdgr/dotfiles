import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from clckwrkbdgr import todo
from clckwrkbdgr.todo import provider
from clckwrkbdgr.todo import tasklist

class TestTask(unittest.TestCase):
	def should_create_task(self):
		task = todo.Task('title')
		self.assertEqual(str(task), 'title')

class TestTaskList(unittest.TestCase):
	def should_add_new_tasks(self):
		original = [
				'Free Liberty statue',
				'Rescue captured agent',
				]
		updated = [
				'Talk to Harley Filben',
				'Free Liberty statue',
				'Rescue captured agent',
				]
		expected = [
				(None, 'Talk to Harley Filben'),
				(True, 'Free Liberty statue'),
				(True, 'Rescue captured agent'),
				]
		self.assertEqual(list(tasklist.filter_task_list(original, updated)), expected)
	def should_remove_missing_tasks(self):
		original = [
				'Talk to Harley Filben',
				'Free Liberty statue',
				'Rescue captured agent',
				]
		updated = [
				'Free Liberty statue',
				'Rescue captured agent',
				]
		expected = [
				(False, 'Talk to Harley Filben'),
				(True, 'Free Liberty statue'),
				(True, 'Rescue captured agent'),
				]
		self.assertEqual(list(tasklist.filter_task_list(original, updated)), expected)
	def should_keep_original_empty_lines_as_separators(self):
		original = [
				'Free Liberty statue',
				'',
				'Rescue captured agent',
				]
		updated = [
				'Free Liberty statue',
				'',
				'Rescue captured agent',
				]
		expected = [
				(True, 'Free Liberty statue'),
				(True, ''),
				(True, 'Rescue captured agent'),
				]
		self.assertEqual(list(tasklist.filter_task_list(original, updated)), expected)
	def should_skip_empty_lines_at_beginning(self):
		original = [
				'',
				'Free Liberty statue',
				'Rescue captured agent',
				]
		updated = [
				'',
				'Free Liberty statue',
				'Rescue captured agent',
				]
		expected = [
				(False, ''),
				(True, 'Free Liberty statue'),
				(True, 'Rescue captured agent'),
				]
		self.assertEqual(list(tasklist.filter_task_list(original, updated)), expected)
	def should_merge_consequent_empty_lines(self):
		original = [
				'Free Liberty statue',
				'',
				'',
				'Rescue captured agent',
				]
		updated = [
				'Free Liberty statue',
				'',
				'',
				'Rescue captured agent',
				]
		expected = [
				(True, 'Free Liberty statue'),
				(True, ''),
				(False, ''),
				(True, 'Rescue captured agent'),
				]
		self.assertEqual(list(tasklist.filter_task_list(original, updated)), expected)
