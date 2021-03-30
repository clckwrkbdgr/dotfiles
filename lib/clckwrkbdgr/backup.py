import contextlib

class Password(object):
	""" Encapsulates password so the actual value would not be present in stack traces.
	Real value is available only via str() within .disclosed() context manager.
	"""
	DUMMY = '*'*8
	def __init__(self, value):
		self.__value = value
		self.__disclosed = False
	@contextlib.contextmanager
	def disclosed(self):
		self.__disclosed = True
		try:
			yield
		finally:
			self.__disclosed = False
	def __str__(self):
		if self.__disclosed:
			return self.__value
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
