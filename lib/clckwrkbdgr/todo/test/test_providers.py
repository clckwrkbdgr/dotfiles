import json
from ... import xdg
from ... import unittest
from ..provider import todo_dir
from .. import _base

class TestTodoDir(unittest.fs.TestCase):
	MODULES = [todo_dir]
	def setUp(self):
		if _base.task_provider._entries.get('todo_dir'): # pragma: no cover
			del _base.task_provider._entries['todo_dir']
		super(TestTodoDir, self).setUp()
	def tearDown(self):
		if _base.task_provider._entries.get('todo_dir'): # pragma: no cover
			del _base.task_provider._entries['todo_dir']

	@unittest.mock.patch('clckwrkbdgr.todo._base.read_config', new=_base.read_config.__wrapped__)
	def should_list_todo_dir(self):
		self.fs.create_file(str(xdg.save_data_path('todo')/'config.json'), contents=json.dumps({
			"inbox_file" : str(xdg.save_data_path('todo')/"inbox.txt"),
			"todo_dir" : str(xdg.save_data_path('todo')),
		}))
		self.fs.create_dir(str(xdg.save_data_path('todo')/'foo'))
		self.fs.create_file(str(xdg.save_data_path('todo')/'bar.md'))
		self.fs.create_file(str(xdg.save_data_path('todo')/'inbox.txt'))

		self.assertEqual(set(todo_dir.list_todo_directory()), {
			_base.Task('foo', tags=['foo']),
			_base.Task('bar.md', tags=['bar']),
			})
