import os
import json
import datetime
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
from clckwrkbdgr import xdg

class UserService(object): # pragma: no cover -- TODO
	def __init__(self, service_id):
		""" Creates interface for service with given ID.
		Reads configuration for service definition file.
		If no definition was found, raises RuntimeError.

		Available fields:
		- id: system service ID, which it registered under.
		  Should match base name of the definition file.
		- modification_time: datetime of the last modification of def. file.
		Following fields should be defined in def. file:
		- display_name: pretty name which will be displayed in management app if there is one.
		  By default matches ID.
		- description: textual description of the service.
		  By default is empty.
		- commandline: list of strings, first value should be proper Windows executable (shell expansion does not work).
		  Tilde and environment variables are expanded.
		  Mandatory option.
		- logfile: path to file where all stdout and stderr will be redirected to.
		  Tilde and environment variables are expanded.
		  Mandatory option.
		- rootdir: Optional root directory to run service in.
		  Tilde and environment variables are expanded.
		"""
		self.id = service_id
		self._load(self.id)
	def _load(self, service_id):
		definition_file = self._find_def_file(service_id)
		if not definition_file:
			raise RuntimeError("Failed to find definition file for service {0}".format(service_id))
		self.modification_time = datetime.datetime.fromtimestamp(definition_file.stat().st_mtime)
		definition = self._read_def_file(definition_file)
		self.display_name = definition.get('display_name')
		self.description = definition.get('description')
		self.commandline = list(map(self._normpath, definition['commandline']))
		self.logfile = definition['logfile']
		self.logfile = self._normpath(self.logfile)
		self.rootdir = definition.get('rootdir')
		if self.rootdir:
			self.rootdir = self._normpath(self.rootdir)
	@staticmethod
	def _normpath(path):
		return os.path.normpath(
				os.path.expandvars(
					os.path.expanduser(
						path
						)))
	def _read_def_file(self, filename):
		return json.loads(filename.read_text())
	def _find_def_file(self, service_id):
		paths = [
				xdg.save_data_path('userservice'),
				Path('~/.local/share/userservice').expanduser(),
				xdg.save_config_path('userservice'),
				]
		for dirname in paths:
			filename = dirname/(service_id+'.json')
			if filename.exists():
				return filename
		return None

	def is_installed(self): # pragma: no cover
		""" Should return True if service is installed in the system and ready to start. """
		raise NotImplementedError
	def install(self): # pragma: no cover
		""" Should initialize and install service into the system. """
		raise NotImplementedError
	def uninstall(self): # pragma: no cover
		""" Should remove service from the system. """
		raise NotImplementedError
	def is_started(self): # pragma: no cover
		""" Should return True if service is already started. """
		raise NotImplementedError
	def start(self): # pragma: no cover
		""" Should send 'start' command to service. """
		raise NotImplementedError
	def stop(self): # pragma: no cover
		""" Should send 'stop' command to service. """
		raise NotImplementedError
