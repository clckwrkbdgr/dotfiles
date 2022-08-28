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

	def should_list_todo_dir(self):
		self.fs.create_file(str(xdg.save_data_path('todo')/'config.json'), contents="""
		{{
			"inbox_file" : "{0}/inbox.txt",
			"todo_dir" : "{0}"
		}}
		""".format(xdg.save_data_path('todo')))
		self.fs.create_dir(str(xdg.save_data_path('todo')/'foo'))
		self.fs.create_file(str(xdg.save_data_path('todo')/'bar.md'))
		self.fs.create_file(str(xdg.save_data_path('todo')/'inbox.txt'))

		self.assertEqual(set(todo_dir.list_todo_directory()), {
			_base.Task('foo'),
			_base.Task('bar.md'),
			})
