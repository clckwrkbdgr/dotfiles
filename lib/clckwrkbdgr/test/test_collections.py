import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from clckwrkbdgr.collections import AutoRegistry

class TestAutoRegistry(unittest.TestCase):
	def should_register_entry(self):
		reg = AutoRegistry()
		@reg('foo')
		def foo_function(): # pragma: no cover
			pass
		self.assertEqual(reg['foo'], foo_function)
	def should_raise_on_attempt_to_rebind_name(self):
		reg = AutoRegistry()
		@reg('foo')
		def foo_function(): # pragma: no cover
			pass
		with self.assertRaises(KeyError):
			@reg('foo')
			def bar_function(): # pragma: no cover
				pass
		self.assertEqual(reg['foo'], foo_function)
	def should_list_registered_entries(self):
		reg = AutoRegistry()
		@reg('foo')
		def foo_function(): # pragma: no cover
			pass
		@reg('bar')
		def bar_function(): # pragma: no cover
			pass
		self.assertEqual(set(reg.keys()), {'foo', 'bar'})
		self.assertEqual(set(reg), {'foo', 'bar'})
