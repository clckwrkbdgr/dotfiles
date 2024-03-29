import os
import datetime
from ... import unittest
from ... import xdg
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
import re
from .. import _base as todo
from .. import search, search_plugins
from .. import provider
from .. import tasklist

class TestPriority(unittest.TestCase):
	def should_init_priority(self):
		priority = todo.Priority()
		self.assertFalse(priority.important)
		self.assertFalse(priority.urgent)
		self.assertIsNone(priority.deadline)
		self.assertFalse(priority.hard)
		self.assertEqual(priority.order, float('inf'))

		priority = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 31, 23, 59),
				hard=True,
				order=100,
				)
		self.assertTrue(priority.important)
		self.assertTrue(priority.urgent)
		self.assertEqual(priority.deadline, datetime.datetime(2020, 12, 31, 23, 59))
		self.assertTrue(priority.hard)
		self.assertEqual(priority.order, 100)
		self.assertEqual(str(priority), '!U(2020-12-31 23:59:00)*:100')
		self.assertEqual(repr(priority), 'Priority(important=True, urgent=True, deadline=datetime.datetime(2020, 12, 31, 23, 59), hard=True, order=100)')

		priority = todo.Priority(
				important=True,
				deadline=datetime.datetime(2020, 12, 31, 23, 59),
				hard=True,
				)
		self.assertEqual(str(priority), '!(2020-12-31 23:59:00)*')
		self.assertEqual(repr(priority), 'Priority(important=True, deadline=datetime.datetime(2020, 12, 31, 23, 59), hard=True)')

		with self.assertRaises(ValueError):
			todo.Priority(deadline='not a proper date')

		with self.assertRaises(ValueError):
			todo.Priority(order=-1)
	def should_store_priorities_in_set(self):
		tasks = {
				todo.Priority(important=True),
				todo.Priority(urgent=True),
				}
		self.assertEqual(tasks, {
			todo.Priority(urgent=True),
			todo.Priority(important=True),
			})
	def should_compare_and_order_priorities(self):
		priority = todo.Priority()
		self.assertEqual(priority.key(), (False, False, datetime.timedelta(), False, -float('inf')))

		priority = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 31, 23, 59),
				hard=True,
				order=100,
				)
		self.assertEqual(priority.key(), (True, True, datetime.timedelta(days=2914269, seconds=59, microseconds=999999), True, -100))

		priority = todo.Priority(
				important=True,
				deadline=datetime.datetime(2020, 12, 31, 23, 59),
				hard=True,
				)
		self.assertEqual(priority.key(), (True, False, datetime.timedelta(days=2914269, seconds=59, microseconds=999999), True, -float('inf')))

		more = todo.Priority(
				important=True,
				)
		less = todo.Priority(
				important=False,
				)
		self.assertTrue(more > less)

		more = todo.Priority(
				important=True,
				urgent=True,
				)
		less = todo.Priority(
				important=True,
				urgent=False,
				)
		self.assertTrue(more > less)

		more = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 31),
				)
		less = todo.Priority(
				important=True,
				urgent=True,
				)
		self.assertTrue(more > less)

		more = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 30),
				)
		less = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 31),
				)
		self.assertTrue(more > less)

		more = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 30),
				hard=True,
				)
		less = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 31),
				)
		self.assertTrue(more > less)

		more = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 30),
				hard=True,
				order=0,
				)
		less = todo.Priority(
				important=True,
				urgent=True,
				deadline=datetime.datetime(2020, 12, 31),
				hard=True,
				order=1,
				)
		self.assertTrue(more > less)

class TestTask(unittest.TestCase):
	def should_create_task(self):
		task = todo.Task('title')
		self.assertEqual(str(task), 'title')
		self.assertEqual(repr(task), 'Task({0}, Priority())'.format(repr('title')))

		task = todo.Task('title', priority=todo.Priority(urgent=True), tags=['tag', 666])
		self.assertEqual(str(task), 'title')
		self.assertEqual(repr(task), 'Task({0}, Priority(urgent=True), tags={1})'.format(repr('title'), repr({'tag', '666'})))
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

class TestConfig(unittest.fs.TestCase):
	MODULES = [todo, xdg]
	@unittest.mock.patch.dict('os.environ', {
		'EDITOR':'myeditor',
		'MYVAR':'myvalue',
		}, clear=True)
	@unittest.mock.patch('os.path.expandvars', new=lambda p: p.replace('$MYVAR', 'myvalue'))
	@unittest.mock.patch('importlib.import_module')
	def should_read_config(self, import_module):
		config = todo.read_config.__wrapped__()
		self.assertEqual(set(config.keys()), {'tasklist', 'todo_dir', 'task_providers', 'inbox_file', 'prepend_inbox', 'editor'})
		self.assertEqual(config.inbox_file, Path("~/.local/share/todo/.INBOX.md").expanduser())
		self.assertEqual(config.prepend_inbox, False)
		self.assertEqual(config.editor, ["myeditor"])
		self.assertEqual(config.todo_dir, Path("~/.local/share/todo/").expanduser())
		self.assertEqual(config.task_providers, [])
		self.assertEqual(config.tasklist, None)

		self.fs.create_file(str(xdg.save_data_path('todo')/'config.json'), contents="""
		{
			"inbox_file" : "~/$MYVAR/inbox.txt",
			"prepend_inbox" : true,
			"editor" : ["vim", "+cw"],
			"todo_dir" : "~/$MYVAR",
			"tasklist" : "my_module.MyTaskList",
			"task_providers" : [
				"foo",
				"bar"
			]
		}
		""")

		MyTaskList = unittest.mock.MagicMock()
		mock_module = unittest.mock.MagicMock(MyTaskList=MyTaskList)
		import_module.side_effect = [ImportError, mock_module]

		config = todo.read_config.__wrapped__()
		self.assertEqual(set(config.keys()), {'tasklist', 'todo_dir', 'task_providers', 'inbox_file', 'prepend_inbox', 'editor'})
		self.assertEqual(config.inbox_file, Path("~/myvalue/inbox.txt").expanduser())
		self.assertEqual(config.prepend_inbox, True)
		self.assertEqual(config.editor, ["vim", "+cw"])
		self.assertEqual(config.todo_dir, Path("~/myvalue").expanduser())
		self.assertEqual(config.task_providers, ["foo", "bar"])
		self.assertEqual(config.tasklist, MyTaskList)

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

class TestTaskListInFileSystem(unittest.fs.TestCase):
	MODULES = [tasklist]
	@unittest.mock.patch('clckwrkbdgr.todo.tasklist.force_load_task_providers')
	def should_list_tasklist_content(self, _):
		tasks = tasklist.TaskList()
		self.assertEqual(list(tasks.list_all()), [])

		self.fs.create_file(str(xdg.save_state_path('todo')/'tasklist.lst'), contents="foo\n\nbar\nbaz")
		self.assertEqual(list(tasks.list_all()), [
			todo.Task('foo'),
			todo.Task('bar'),
			todo.Task('baz'),
			])
		self.assertEqual(list(tasks.list_all(with_groups=True)), [
			todo.Task('foo'),
			[todo.Task('bar'), todo.Task('baz')],
			])
	@unittest.mock.patch('os.environ.get', new=lambda name,*_: {
		'EDITOR':'myeditor',
		}[name])
	@unittest.mock.patch('os.path.expandvars', new=lambda p: p.replace('$MYVAR', 'myvalue'))
	@unittest.mock.patch('platform.system', side_effect=['Windows'])
	@unittest.mock.patch('subprocess.call', side_effect=[0])
	@unittest.mock.patch('clckwrkbdgr.todo.tasklist.force_load_task_providers')
	def should_sort_tasklist_in_external_editor(self, _, subprocess_call, platform_system):
		self.fs.create_file(str(xdg.save_data_path('todo')/'config.json'), contents="""
		{
			"inbox_file" : "~/$MYVAR/inbox.txt",
			"editor" : ["vim", "+cw"],
			"todo_dir" : "~/$MYVAR"
		}
		""")

		tasks = tasklist.TaskList()
		self.assertTrue(tasks.sort())
		subprocess_call.assert_called_with(
				['vim', '+cw', str(xdg.save_state_path('todo')/'tasklist.lst')], shell=True,
				)
	@unittest.mock.patch('clckwrkbdgr.todo._base.task_provider')
	@unittest.mock.patch('clckwrkbdgr.todo.tasklist.force_load_task_providers')
	def should_sync_tasklist(self, _, task_provider):
		self.fs.create_dir(str(xdg.save_state_path('todo')))

		tasks = tasklist.TaskList()

		mock_providers = [
				(lambda: [todo.Task('foo'), todo.Task('bar')]),
				(lambda: [todo.Task('hello'), todo.Task('world')]),
				]
		task_provider.__iter__ = lambda _: iter(mock_providers)

		tasks.sync()
		self.assertEqual((xdg.save_state_path('todo')/'tasklist.lst').read_text(), '\n'.join([
			"foo",
			"bar",
			"hello",
			"world",
			]) + '\n')

		tasks.sync()
		self.assertEqual((xdg.save_state_path('todo')/'tasklist.lst').read_text(), '\n'.join([
			"foo",
			"bar",
			"hello",
			"world",
			]) + '\n')

		(xdg.save_state_path('todo')/'tasklist.lst').write_text(u"foo\n\nbar")
		tasks.sync()
		self.assertEqual((xdg.save_state_path('todo')/'tasklist.lst').read_text(), '\n'.join([
			"hello",
			"world",
			"foo",
			"",
			"bar",
			]) + '\n')

		(xdg.save_state_path('todo')/'tasklist.lst').write_text(u"foo\n\nbaz")
		tasks.sync()
		self.assertEqual((xdg.save_state_path('todo')/'tasklist.lst').read_text(), '\n'.join([
			"bar",
			"hello",
			"world",
			"foo",
			]) + '\n')

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
