from clckwrkbdgr import todo
from clckwrkbdgr.todo import provider
from clckwrkbdgr.todo import tasklist
import unittest

class TestTask(unittest.TestCase):
	def should_create_task(self):
		task = todo.Task('title')
		self.assertEqual(str(task), 'title')
