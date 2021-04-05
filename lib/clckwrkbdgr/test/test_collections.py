import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import pickle
from clckwrkbdgr.collections import AutoRegistry
from clckwrkbdgr.collections import dotdict

class TestDotDict(unittest.TestCase):
	def should_access_dotdict_fields_via_dot(self):
		d = dotdict()
		d['field'] = 'foo'
		self.assertEqual(d.field, 'foo')
		self.assertEqual(d['field'], 'foo')
	def should_create_dotdict_from_base_dict(self):
		d = dotdict({'field':'foo'})
		self.assertEqual(d.field, 'foo')
		self.assertEqual(d['field'], 'foo')
	def should_set_dotdict_fields_via_dot(self):
		d = dotdict({'field':'foo'})
		d.field = 'foo'
		self.assertEqual(d.field, 'foo')
		self.assertEqual(d['field'], 'foo')
	def should_convert_nested_dicts_to_dotdicts(self):
		d = dotdict({'field':'foo', 'nested' : {'subfield': 'bar'}})
		self.assertEqual(d.field, 'foo')
		self.assertEqual(d.nested.subfield, 'bar')
	def should_pickle_and_unpickle_dotdict(self):
		d = dotdict({'field':'foo', 'nested' : {'subfield': 'bar'}})
		data = pickle.dumps(d)
		other = pickle.loads(data)
		self.assertEqual(d, other)
		self.assertTrue(type(other) is dotdict)
		self.assertTrue(type(other.nested) is dotdict)

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
		self.assertEqual(set(reg.values()), {foo_function, bar_function})
		self.assertEqual(set(reg), {foo_function, bar_function})
		self.assertEqual(set(reg.items()), {('foo', foo_function), ('bar', bar_function)})
