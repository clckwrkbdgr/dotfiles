import datetime

class Logger: # pragma: no cover -- TODO
	def __init__(self):
		self.fd = None
	def log(self, levelname, message):
		if not self.fd:
			return
		self.fd.write('{asctime}:{levelname}: {message}\n'.format(
			asctime=datetime.datetime.now().isoformat(),
			levelname=levelname,
			message=message,
			))
		self.fd.flush()
	def debug(self, message): self.log('debug', message)
	def info(self, message): self.log('debug', message)
	def warning(self, message): self.log('debug', message)
	def error(self, message): self.log('debug', message)
	def init(self, filename):
		if self.fd:
			self.fd.close()
		self.fd = open(filename, 'w')

Log = Logger()
