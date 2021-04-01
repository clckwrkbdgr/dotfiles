import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from clckwrkbdgr.backup import Password, PasswordArg

class TestPassword(unittest.TestCase):
	def should_hide_password_by_default(self):
		real_value = 'qwerty'
		passwd = Password(real_value)
		self.assertTrue(passwd)
		self.assertEqual(str(passwd), Password.DUMMY)
		self.assertEqual(repr(passwd), 'Password({0})'.format(Password.DUMMY))
		self.assertFalse(real_value in str(dir(passwd)))
		class Container:
			def __init__(self, value):
				self.value = value
		container = Container(passwd)
		self.assertFalse(real_value in str(container.__dict__))
	def should_disclose_password(self):
		real_value = 'qwerty'
		passwd = Password(real_value)
		with passwd.disclosed():
			self.assertEqual(str(passwd), real_value)
			self.assertEqual(repr(passwd), 'Password({0})'.format(Password.DUMMY))
			self.assertFalse(real_value in str(dir(passwd)))
			class Container:
				def __init__(self, value):
					self.value = value
			container = Container(passwd)
			self.assertFalse(real_value in str(container.__dict__))
		self.assertEqual(str(passwd), Password.DUMMY)
	def should_handle_no_password(self):
		none = Password(None)
		self.assertFalse(none)
		self.assertEqual(str(none), Password.DUMMY)
		with none.disclosed():
			self.assertEqual(str(none), '')
	def should_copy_password(self):
		real_value = 'qwerty'
		passwd = Password(Password(real_value))
		with passwd.disclosed():
			self.assertEqual(str(passwd), real_value)
	def should_accept_only_strings(self):
		with self.assertRaises(TypeError):
			Password(list())
	def should_protect_password_in_subprocess_args(self):
		real_value = 'qwerty'
		passwd = Password(real_value)
		arg = PasswordArg(passwd)

		self.assertEqual(str(arg), '-p' + Password.DUMMY)
		self.assertEqual(repr(arg), repr(passwd))
		with passwd.disclosed():
			self.assertEqual(str(arg), '-p' + real_value)
		self.assertEqual(str(arg), '-p' + Password.DUMMY)
