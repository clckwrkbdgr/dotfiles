import contextlib

class Password(object):
	""" Encapsulates password so the actual value would not be present in stack traces.
	Real value is available only via str() within .disclosed() context manager.
	"""
	DUMMY = '*'*8
	def __init__(self, value):
		""" If value is None, essentially disables the password.
		bool(Password(None)) will return False and disclosed password will be empty string.
		"""
		self.__disclosed = False
		if isinstance(value, Password):
			self.__value = value.__value
			return
		if value is not None and not isinstance(value, str):
			raise TypeError('Expected password of type str, received {0}'.format(type(value)))
		self.__value = value
	def __bool__(self):
		return self.__value is not None
	__nonzero__ = __bool__
	@contextlib.contextmanager
	def disclosed(self):
		self.__disclosed = True
		try:
			yield
		finally:
			self.__disclosed = False
	def __str__(self):
		if self.__disclosed:
			return self.__value or ''
		return self.DUMMY
	def __repr__(self):
		return "Password({0})".format(self.DUMMY)

class PasswordArg(object):
	""" To prevent storing password as plain text variable
	up until command line is formed for the subprocess call.
	"""
	def __init__(self, password):
		self.password = password
	def __str__(self):
		return '-p{0}'.format(self.password)
	def __repr__(self):
		return repr(self.password)
