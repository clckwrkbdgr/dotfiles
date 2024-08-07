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
	def __str__(self):
		return 'Discovered {0}'.format(str(self.obj))

class AttackEvent(Event):
	def __init__(self, actor, target):
		self.actor = actor
		self.target = target
	def __str__(self):
		return '{0} attacks {1}'.format(str(self.actor), str(self.target))

class HealthEvent(Event):
	def __init__(self, target, diff):
		self.target = target
		self.diff = diff
	def __str__(self):
		return '{0} {1:+} hp'.format(str(self.target), self.diff)

class DeathEvent(Event):
	def __init__(self, target):
		self.target = target
	def __str__(self):
		return '{0} dies'.format(str(self.target))

class MoveEvent(Event):
	def __init__(self, actor, dest):
		self.actor = actor
		self.dest = dest
	def __str__(self):
		return '{0} moves to {1}'.format(str(self.actor), self.dest)

class DescendEvent(Event):
	def __init__(self, actor):
		self.actor = actor
	def __str__(self):
		return '{0} descends'.format(self.actor)

class BumpEvent(Event):
	def __init__(self, actor, dest):
		self.actor = actor
		self.dest = dest
	def __str__(self):
		return '{0} bumps into {1}'.format(str(self.actor), self.dest)

class GrabItemEvent(Event):
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} grabs {1}'.format(self.actor, self.item)

class ConsumeItemEvent(Event):
	def __init__(self, actor, item):
		self.actor = actor
		self.item = item
	def __str__(self):
		return '{0} consumes {1}'.format(self.actor, self.item)
