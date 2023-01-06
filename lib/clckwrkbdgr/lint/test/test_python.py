from ... import unittest
from .. import python

class TestPythonSyntax(unittest.fs.TestCase):
	MODULES = [python]
	def should_check_python_syntax(self):
		self.fs.create_file('/good.py', contents='print("Hello world")')
		self.fs.create_file('/bad.py', contents='print("Hello world')
		self.assertTrue(python.check_syntax('/good.py', quiet=True))
		self.assertFalse(python.check_syntax('/bad.py', quiet=True))
