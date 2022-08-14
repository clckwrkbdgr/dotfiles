from clckwrkbdgr import unittest
import re
from clckwrkbdgr import todo
from clckwrkbdgr.todo import search
from clckwrkbdgr.todo import provider
from clckwrkbdgr.todo import tasklist

class TestTask(unittest.TestCase):
	def should_create_task(self):
		task = todo.Task('title')
		self.assertEqual(str(task), 'title')
	def should_compare_and_order_tasks(self):
		tasks = [
				todo.Task('foo'),
				todo.Task('bar'),
				todo.Task('baz'),
				]
		self.assertEqual(sorted(tasks), [
			todo.Task('bar'),
			todo.Task('baz'),
			todo.Task('foo'),
			])
	def should_store_tasks_in_set(self):
		tasks = {
				todo.Task('foo'),
				todo.Task('bar'),
				todo.Task('baz'),
				}
		self.assertEqual(tasks, {
			todo.Task('bar'),
			todo.Task('baz'),
			todo.Task('foo'),
			})

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

class TestSearch(unittest.TestCase):
	def should_search_in_string(self):
		self.assertEqual(
				search.search_in_line('foo bar baz', re.compile('(bar)')),
				['foo ', 'bar', ' baz'],
				)
		self.assertEqual(
				search.search_in_line('foo bar baz', re.compile('(baz)')),
				['foo bar ', 'baz', ''],
				)
		self.assertEqual(
				search.search_in_line('foo bar baz', re.compile(r'(\W)')),
				['foo', ' ', 'bar', ' ', 'baz'],
				)
		self.assertIsNone(
				search.search_in_line('foo bar baz', re.compile(r'(will to live)')),
				)
	def should_search_in_bytes(self):
		self.assertEqual(
				list(search.search_in_bytes(b'foo\nbar\nbaz\n', re.compile('(a[rz])'))),
				[
					(2, ['b', 'ar', '']),
					(3, ['b', 'az', '']),
					],
				)

class TestSearchInFiles(unittest.fs.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[search])
	def should_search_in_bytes(self):
		self.fs.create_file('/test_file', contents=b'foo\nbar\nbaz\n')
		self.assertEqual(
				list(search.search_in_file('/test_file', re.compile('(a[rz])'))),
				[
					(2, ['b', 'ar', '']),
					(3, ['b', 'az', '']),
					],
				)
		self.assertEqual(
				list(search.search_in_file('/absent_file', re.compile('(a[rz])'))),
				[],
				)
