import datetime

class Logger:
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
	def info(self, message): self.log('info', message)
	def warning(self, message): self.log('warning', message)
	def error(self, message): self.log('error', message)
	def init(self, filename):
		if self.fd:
			self.fd.close()
		self.fd = open(filename, 'w')

Log = Logger()

class Event(object):
	pass

class DiscoverEvent(Event):
	def __init__(self, obj):
		self.obj = obj

class AttackEvent(Event):
	def __init__(self, actor, target):
		self.actor = actor
		self.target = target

class HealthEvent(Event):
	def __init__(self, target, diff):
		self.target = target
		self.diff = diff

class DeathEvent(Event):
	def __init__(self, target):
		self.target = target
