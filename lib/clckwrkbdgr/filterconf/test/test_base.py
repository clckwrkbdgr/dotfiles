import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from .. import _base

class TestEnvironment(unittest.TestCase):
	def should_register_loader_callbacks(self):
		env = _base.Environment()
		env.register('MY_VAR', lambda: 'my_value')
		self.assertEqual(set(env.known_names()), {'MY_VAR'})
	def should_get_value_using_callback(self):
		env = _base.Environment()
		env.register('MY_VAR', lambda: 'my_value')
		self.assertEqual(env.get('MY_VAR'), 'my_value')
	def should_cache_calculated_value(self):
		env = _base.Environment()
		def callback():
			callback.value += 1
			return str(callback.value)
		callback.value = 0
		env.register('MY_VAR', callback)
		self.assertEqual(env.get('MY_VAR'), '1')
		self.assertEqual(env.get('MY_VAR'), '1')

class TestConfigFilter(unittest.TestCase):
	def should_prepare_description_from_docstring(self):
		class MockFilter(_base.ConfigFilter): # pragma: no cover
			""" Main description. """
			def sort(self):
				""" Sort description. """
		self.assertEqual(MockFilter.description(), 'Main description. \nSort description. ')
