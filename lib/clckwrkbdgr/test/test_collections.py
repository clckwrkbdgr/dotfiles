from clckwrkbdgr import unittest
import pickle
from clckwrkbdgr.collections import AutoRegistry
from clckwrkbdgr.collections import dotdict
from clckwrkbdgr.collections import Enum, DocstringEnum

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
	def should_convert_deep_nested_dicts_to_dotdicts(self):
		d = dotdict.deep({
			'field':'foo',
			'nested' : {'subfield': 'bar'},
			'sublist' : [
				{'subfield': 'baz'},
				],
			})
		self.assertEqual(d.field, 'foo')
		self.assertEqual(d.nested.subfield, 'bar')
		self.assertEqual(d.sublist[0].subfield, 'baz')
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
	def should_register_entry_with_autoguessed_name(self):
		reg = AutoRegistry()
		@reg()
		def foo_function(): # pragma: no cover
			pass
		@reg()
		class FooClass: # pragma: no cover
			pass
		self.assertEqual(reg['foo_function'], foo_function)
		self.assertEqual(reg['FooClass'], FooClass)

		with self.assertRaises(ValueError):
			reg()('not a named object')
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

class TestEnumeration(unittest.TestCase):
	def should_create_enum(self):
		class MyEnum(Enum):
			auto = Enum.auto(3)
			FIRST = auto()
			SECOND = auto()
			THIRD = auto()
		self.assertEqual(MyEnum.FIRST, 3)
		self.assertEqual(MyEnum.SECOND, 4)
		self.assertEqual(MyEnum.THIRD, 5)
		self.assertEqual(MyEnum._top(), 5)
		self.assertEqual(MyEnum._all(), {'FIRST':3, 'SECOND':4, 'THIRD':5})
		class MyOtherEnum(Enum):
			auto = Enum.auto()
			FIRST = auto()
			SECOND = auto()
		self.assertEqual(MyOtherEnum.FIRST, 1)
		self.assertEqual(MyOtherEnum.SECOND, 2)
		self.assertEqual(MyOtherEnum._top(), 2)
		self.assertEqual(MyOtherEnum._all(), {'FIRST':1, 'SECOND':2})
	def should_create_enumeration(self):
		class MyEnum(DocstringEnum):
			"""
			first
			Second
			"""
		self.assertEqual(MyEnum.FIRST, 0)
		self.assertEqual(MyEnum.SECOND, 1)
		self.assertEqual(MyEnum.CURRENT, 2)
