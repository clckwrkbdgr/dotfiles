import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import clckwrkbdgr.utils as utils

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
