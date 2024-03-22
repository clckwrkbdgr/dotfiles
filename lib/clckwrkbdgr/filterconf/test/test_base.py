from clckwrkbdgr import unittest
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

class TestUtils(unittest.TestCase):
	def should_convert_pattern_by_type(self):
		regex = _base.convert_pattern('[a-z]+', 'regex')
		self.assertTrue(regex.match('foo'))
		self.assertFalse(regex.match('123 foo'))
		self.assertTrue(regex.search('123 foo'))

		wildcard = _base.convert_pattern('[a-z][a-z][a-z]', 'wildcard')
		self.assertTrue(wildcard.match('foo'))
		self.assertFalse(wildcard.match('123 foo'))
		self.assertTrue(wildcard.search('123 foo'))

		plain = _base.convert_pattern('foo')
		self.assertTrue(plain.match('foo'))
		self.assertFalse(plain.match('123 foo'))
		self.assertTrue(plain.search('123 foo'))

class TestConfigFilter(unittest.TestCase):
	def should_prepare_description_from_docstring(self):
		class MockFilter(_base.ConfigFilter): # pragma: no cover
			""" Main description. """
			def sort(self):
				""" Sort description. """
		self.assertEqual(MockFilter.description(), 'Main description. \nSort description. ')
