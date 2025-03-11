from clckwrkbdgr import unittest
import clckwrkbdgr.utils as utils

class CustomType:
	pass

custom_var = 'foo'

class TestUtils(unittest.TestCase):
	def should_detect_collections(self):
		self.assertFalse(utils.is_collection(None))
		self.assertFalse(utils.is_collection('123'))
		self.assertFalse(utils.is_collection(123))
		self.assertTrue(utils.is_collection([1, 2, 3]))
		self.assertTrue(utils.is_collection((1, 2, 3)))
		self.assertTrue(utils.is_collection({1, 2, 3}))
		self.assertTrue(utils.is_collection({1:1, 2:2, 3:3}))
		self.assertTrue(utils.is_collection([]))
	def should_get_type_by_name(self):
		self.assertTrue(utils.get_type_by_name("str") is str)
		self.assertTrue(utils.get_type_by_name("CustomType") is CustomType)
		self.assertTrue(utils.get_type_by_name("unittest.TestCase") is unittest.TestCase)
		with self.assertRaises(RuntimeError):
			utils.get_type_by_name("unknown type name")
		with self.assertRaises(RuntimeError):
			utils.get_type_by_name("custom_var")
	def should_get_type_by_name_from_outer_frames(self):
		def subframe(name, frame_correction):
			return utils.get_type_by_name(name, frame_correction=frame_correction)
		self.assertTrue(subframe("CustomType", 1) is CustomType)
		self.assertTrue(subframe("TestCase", 2) is unittest.TestCase)
	def should_define_class_level_field(self):
		class BaseField:
			name = utils.classfield('_name', 'default')
		class CustomField(BaseField):
			_name = "custom"
		class DefaultField(BaseField):
			pass
		self.assertEqual(CustomField().name, 'custom')
		self.assertEqual(DefaultField().name, 'default')
	def should_split_sequence_to_chunks(self):
		self.assertEqual(list(utils.chunks(['a', 'b', 'c', 'd'], 2)), [['a', 'b'], ['c', 'd']])
		self.assertEqual(list(utils.chunks(('a', 'b', 'c', 'd'), 2)), [('a', 'b'), ('c', 'd')])
		self.assertEqual(list(utils.chunks('abcd', 2)), ['ab', 'cd'])
		self.assertEqual(list(utils.chunks('abcd', 3, '_')), ['abc', 'd__'])
		self.assertEqual(list(utils.chunks('abcd', 3, pad=False)), ['abc', 'd'])
		self.assertEqual(list(utils.chunks((_ for _ in 'abcd'), 2)), [('a', 'b'), ('c', 'd')])
	def should_detect_integer_values(self):
		self.assertTrue(utils.is_integer(0))
		self.assertTrue(utils.is_integer(1))
		self.assertTrue(utils.is_integer(float(0)))
		self.assertTrue(utils.is_integer(0.0))
		self.assertTrue(utils.is_integer(float(1)))
		self.assertFalse(utils.is_integer('0'))
		self.assertFalse(utils.is_integer(1.1))

class TestMetaUtils(unittest.TestCase):
	def should_use_metaclasses(self):
		class _MyMetaClass(type):
			@property
			def value(self):
				return "foobar"
		@utils.with_metaclass(_MyMetaClass)
		class _MyClass(object):
			pass
		self.assertEqual(_MyClass.value, "foobar")
	def should_list_all_subclasses(self):
		class _MyParentClass(object): pass
		class _MyDirectChild(_MyParentClass): pass
		class _MyDirectChildParent(_MyParentClass): pass
		class _MyNonDirectChild(_MyParentClass): pass
		self.assertEqual(sorted(utils.all_subclasses(_MyParentClass), key=lambda cls: cls.__name__), [
			_MyDirectChild,
			_MyDirectChildParent,
			_MyNonDirectChild,
			])
class TestExitCode(unittest.TestCase):
	def should_convert_None_to_0(self):
		self.assertEqual(utils.convert_to_exit_code(None), 0)
	def should_convert_True_to_0(self):
		self.assertEqual(utils.convert_to_exit_code(True), 0)
	def should_convert_False_to_1(self):
		self.assertEqual(utils.convert_to_exit_code(False), 1)
	def should_return_int_as_is(self):
		self.assertEqual(utils.convert_to_exit_code(0), 0)
		self.assertEqual(utils.convert_to_exit_code(1), 1)
		self.assertEqual(utils.convert_to_exit_code(255), 255)
		self.assertEqual(utils.convert_to_exit_code(-1), -1)
	def should_treat_any_other_type_as_bool(self):
		self.assertEqual(utils.convert_to_exit_code(['a']), 0)
		self.assertEqual(utils.convert_to_exit_code([]), 1)
		self.assertEqual(utils.convert_to_exit_code('a'), 0)
		self.assertEqual(utils.convert_to_exit_code(''), 1)
		class _Mock: pass
		self.assertEqual(utils.convert_to_exit_code(_Mock()), 0)
	def should_convert_function_return_value_to_exit_code(self):
		@utils.returns_exit_code
		def func(value):
			return value
		self.assertEqual(func(None), 0)
		self.assertEqual(func(True), 0)
		self.assertEqual(func(False), 1)
		self.assertEqual(func(0), 0)
		self.assertEqual(func(1), 1)
	def should_immediately_exit_from_function_with_converted_return_value(self):
		@utils.exits_with_return_value
		def func(value):
			return value
		with self.assertRaises(SystemExit) as e:
			func(None)
		self.assertEqual(e.exception.code, 0)
		with self.assertRaises(SystemExit) as e:
			func(True)
		self.assertEqual(e.exception.code, 0)
		with self.assertRaises(SystemExit) as e:
			func(False)
		self.assertEqual(e.exception.code, 1)
		with self.assertRaises(SystemExit) as e:
			func(0)
		self.assertEqual(e.exception.code, 0)
		with self.assertRaises(SystemExit) as e:
			func(1)
		self.assertEqual(e.exception.code, 1)

class TestStringUtils(unittest.TestCase):
	def should_quote_string(self):
		self.assertEqual(utils.quote_string(""), '""')
		self.assertEqual(utils.quote_string("   "), '"   "')
		self.assertEqual(utils.quote_string("foo bar", "'"), "'foo bar'")
		self.assertEqual(utils.quote_string("foo bar", '"'), '"foo bar"')
		self.assertEqual(utils.quote_string("foo bar", '"'), '"foo bar"')
		self.assertEqual(utils.quote_string("foo bar", '<', '>'), '<foo bar>')
		self.assertEqual(utils.quote_string("foo <bar>", '<', '>'), r'<foo \<bar\>>')
		self.assertEqual(utils.quote_string("\'foo bar\""), '"\'foo bar\\""')
		self.assertEqual(utils.quote_string("\'foo bar\"", "'"), "'\\\'foo bar\"'")
		self.assertEqual(utils.quote_string("\'foo bar\"", "*"), '*\'foo bar\"*')
	def should_unquote_string(self):
		self.assertEqual(utils.unquote_string('"foobar"'), 'foobar')
		self.assertEqual(utils.unquote_string("'foobar'"), 'foobar')
		self.assertEqual(utils.unquote_string("'foobar"), "'foobar")
