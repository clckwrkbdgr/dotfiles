from . import fs 
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

def send(subject, body, payload=None):
	""" Sends message with given subject and optional payload (attached files): dict of {name: data (str or bytes)} """
	return Provider.current().send(subject, body, payload=payload)

class Provider(object):
	_providers = [] # tuple(priority, type)
	_current = None

	@classmethod
	def qualify(cls): # pragma: no cover
		""" Should return True if providers qualifies in current environment. """
		raise NotImplementedError
	def send(self, subject, body, payload=None): # pragma: no cover
		""" Should send message with given subject and optional payload.
		Should return True upon success.
		"""
		raise NotImplementedError

	@classmethod
	def current(cls):
		""" Returns currently set provider.
		During initial call, picks first available (and qualified) provider starting from the topmost priority.
		"""
		if cls._current is None:
			queue = (provider for _, provider in sorted(cls._providers, key=lambda _:_[0], reverse=True) if provider.qualify())
			cls._current = next(queue)()
		return cls._current
	@classmethod
	def register(cls, priority):
		""" Decorator to register provider class with some priority ([0.0..1.0])
		"""
		assert 0.0 <= priority <= 1.0
		def _actual(provider):
			cls._providers.append( (priority, provider) )
			return provider
		return _actual

@Provider.register(priority=0.0)
class DesktopFile(Provider):
	""" Default and most basic mail provider, just stores message in a file on a desktop.
	"""
	def __init__(self, dest_dir=None):
		""" By default dest dir is XDG_DESKTOP_DIR. """
		from . import xdg 
		self.dest_dir = Path(dest_dir or xdg.XDG_DESKTOP_DIR)
		self.dest_dir.mkdir(parents=True, exist_ok=True)
	@classmethod
	def qualify(cls):
		return True # Works where FS is present, so always.
	def send(self, subject, body, payload=None):
		filename = fs.make_valid_filename(subject)
		dest = fs.make_unique_filename(self.dest_dir/filename)
		dest.write_text(body)
		if payload:
			for name, data in payload.items():
				filename = fs.make_valid_filename(name)
				dest = fs.make_unique_filename(self.dest_dir/filename)
				if hasattr(data, 'encode'):
					data = data.encode('utf-8', 'replace')
				dest.write_bytes(data)
		return True

@Provider.register(priority=0.5)
class MailX(Provider):
	@classmethod
	def qualify(cls):
		try:
			from shutil import which
		except ImportError: # pragma: no cover -- py2
			from .pyshell import which
		return True if which('mail') is not None else False
	def send(self, subject, body, payload=None):
		import getpass
		import subprocess
		mailx = subprocess.Popen(['mail', '-s', str(subject), getpass.getuser()], stdin=subprocess.PIPE)
		data = body.encode('utf-8', 'replace')
		if payload: # pragma: no cover
			raise NotImplementedError("MailX does not send attached files yet.")
		mailx.communicate(data)
		return 0 == mailx.wait()
