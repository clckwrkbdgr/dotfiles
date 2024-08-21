import datetime

class Logger:
	""" Logs messages to log file.

	Offers several logging levels: debug(), info(), warning(), error().

	Default global logger is available as module variable .Log
	"""
	def __init__(self):
		""" Default logger is created without opened file,
		so messages are not written anywhere.
		Call init() to open actual file.
		"""
		self.fd = None
	def log(self, levelname, message):
		""" Basic logging routine.
		Writes current timestamp, log level in addition to the message.
		"""
		if not self.fd:
			return
		self.fd.write('{asctime}:{levelname}: {message}\n'.format(
			asctime=datetime.datetime.now().isoformat(),
			levelname=levelname,
			message=message,
			))
		self.fd.flush()
	def debug(self, message): self.log('debug', message)
	def info(self, message): self.log('info', message)
	def warning(self, message): self.log('warning', message)
	def error(self, message): self.log('error', message)
	def init(self, filename):
		""" Inits (or re-inits) log file to write messages to.
		"""
		if self.fd:
			self.fd.close()
		self.fd = open(filename, 'w')

Log = Logger()
