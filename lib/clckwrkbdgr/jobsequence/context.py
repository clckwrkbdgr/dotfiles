from __future__ import print_function
import os, sys
import logging
import atexit
import clckwrkbdgr.jobsequence.script

def _comply_about_accumulated_return_code(): # pragma: no cover
	if Context._global_return_code != 0:
		print('[jobsequence.context: Return code {0} was prepared but Context.done() was not called]'.format(Context._global_return_code), file=sys.stderr)
atexit.register(_comply_about_accumulated_return_code)

class WorkerStats:
	""" Defines worker host and it's capabilities regarding custom tasks,
	or search parameters to match such hosts.
	"""
	def __init__(self, hostname, caps, logger=None):
		""" Both hostname and caps may be None. """
		self.hostname = hostname
		self.caps = caps
		self._logger = logger or logging
	def __str__(self): # pragma: no cover
		return '{0}:{1}'.format(self.hostname, self.caps)
	def __repr__(self): # pragma: no cover
		return '{0}({1}, {2})'.format(self.__class__.__name__, repr(self.hostname), repr(self.caps))
	def save(self, filename):
		self._logger.debug('Updating worker file: {0}'.format(self))
		with open(str(filename), 'w') as f:
			if self.caps is None:
				f.write('{0}\n'.format(self.hostname))
			else:
				f.write('{0}\n{1}\n'.format(self.hostname, self.caps))
	@classmethod
	def load(cls, filename, caps_type=None, logger=None):
		""" Returns WorkerStats object from given file (if it exists).
		Caps type can be a function that returns caps object, by default caps are str.
		Caps object should be comparable and str-able.

		Worker stats file should have following format:
		1 line:"<hostname>";
		2 line:"<serialized caps>";
		Both lines are optional, defaults are None.
		"""
		logger = logger or logging
		if not os.path.exists(str(filename)):
			logger.debug("{0} does not exist".format(filename))
			return cls(None, None, logger=logger)
		with open(filename) as f:
			stored_host = f.readline().rstrip('\n')
			logger.debug('Stored host: {0}'.format(repr(stored_host)))
			if not stored_host:
				return cls(None, None, logger=logger)
			stored_caps = f.readline().rstrip('\n')
			logger.debug('Stored caps: {0}'.format(repr(stored_caps)))
			if not stored_caps:
				return cls(stored_host, None, logger=logger)
			if caps_type:
				stored_caps = caps_type(stored_caps)
			logger.debug('Converted caps: {0}'.format(repr(stored_caps)))
			return cls(stored_host, stored_caps, logger=logger)
	def is_preferred(self, stored, required_caps=None):
		""" Returns True if current stats are acceptable and current host should be picked as worker host.
		Considers already stored worker stats (if any).
		Considers optional required caps (to filter out "not capable" hosts).
		Returns False otherwise.
		"""
		if stored.hostname is None or self.hostname == stored.hostname:
			self._logger.debug('Stored hostname is empty or the same: {0}'.format(stored.hostname))
			if required_caps is None:
				self._logger.debug('Caps are not required.')
				return True
			if self.caps is None:
				self._logger.debug('Caps are required, but self caps are None.')
				return False
			self._logger.debug('Current caps satisfy requirements: {0}'.format(self.caps >= required_caps))
			return self.caps >= required_caps
		if stored.caps is None:
			self._logger.debug('There were no stored caps.')
			if required_caps is None:
				self._logger.debug('And no caps requirements.')
				return False
			if self.caps is None:
				self._logger.debug('Caps are required, but self caps are None.')
				return False
			self._logger.debug('Current caps satisfy requirements: {0}'.format(self.caps >= required_caps))
			return self.caps >= required_caps
		if self.caps is None:
			self._logger.debug('Current caps are not better than stored: {0} <= {1}'.format(self.caps, stored.caps))
			return False
		if required_caps is None:
			self._logger.debug('There were no caps requirements, skipping check.')
		elif self.caps < required_caps:
			self._logger.debug('Current caps does not satisfy requirements: {0} < {1}'.format(self.caps, required_caps))
			return False
		if self.caps <= stored.caps:
			self._logger.debug('Current caps are not better than stored: {0} <= {1}'.format(self.caps, stored.caps))
			return False
		return True

class Context: # pragma: no cover -- TODO need mocks
	_global_return_code = 0

	def __init__(self, verbose_level=None, logger_name=None, script_rootdir=None):
		self._verbose_level = verbose_level
		self._script_rootdir = script_rootdir

		self._logger = logging.getLogger(logger_name or 'jobsequence')
		if not self._logger.handlers:
			handler = logging.StreamHandler() # TODO custom formatter to display level, module, logger name etc.; and generic clckwrkbdgr module for such loggers.
			self._logger.addHandler(handler)
		if self._verbose_level == 1:
			self._logger.setLevel(logging.INFO)
		elif self._verbose_level is not None and self._verbose_level > 1:
			self._logger.setLevel(logging.DEBUG)
		self._returncode = 0
	def script(self, name=None, shebang=None, rootdir=None, overwrite=True):
		""" Initializes fixer script with given name (by default is taken from the current script)
		and other parameters (see Script help).
		Default rootdir is taken from context parameters (script_rootdir).
		Writes notification about created script to stderr even if not verbose.
		Returns script instance.
		"""
		if not name:
			name = os.path.basename(sys.argv[0])
		if not rootdir:
			rootdir = self._script_rootdir
		script = clckwrkbdgr.jobsequence.script.Script(name, shebang=shebang, rootdir=rootdir, overwrite=overwrite)
		sys.stderr.write("=== Created script: {0}\n".format(script.filename))
		return script
	def done(self):
		""" Immediately exit with accumulated return code.
		By default it will be success.
		See also operator __or__
		If there was some accumulated return code, but this function was never called,
		atexit handler will comply about this fact.
		"""
		Context._global_return_code = 0
		sys.exit(self._returncode)
	def die(self, message, rc=1):
		""" Immediately exit with failure code and given error message. """
		self.critical(message)
		Context._global_return_code = 0
		sys.exit(rc)
	def __or__(self, returncode):
		""" Collects given value as a return code and adds to the global return code.
		Specific values of True or False are treated as 0 and 1 respectfully.
		Sign is collected too and at least one negative return code
		will result in overall negative return code.

		>>> context | subprocess.call(...) # returns 1
		>>> context | subprocess.call(...) # returns -5
		>>> context.done() # exits with -6
		"""
		if returncode is True:
			returncode = 0
		elif returncode is False:
			returncode = 1
		try:
			returncode = int(returncode)
		except:
			import traceback
			traceback.print_exc()
			returncode = 1
		if returncode < 0 and self._returncode > 0:
			self._returncode = -self._returncode
		returncode = abs(returncode)
		if self._returncode < 0:
			self._returncode -= returncode
		else:
			self._returncode += returncode
		Context._global_return_code = self._returncode
	@property
	def quiet(self):
		""" Returns True is verbosity level is less than 1. """
		return self._verbose_level == 0
	@property
	def verbose(self):
		""" Returns verbosity level as int value.
		0 - quiet, 1 - v (verbose), 2 - vv (very verbose) etc.
		"""
		return self._verbose_level
	@property
	def logger(self):
		""" Returns logger object.
		See also debug(), info(), warning(), error(), critical().
		"""
		return self._logger
	def quiet_arg(self, *args):
		""" Returns list of given args if quiet, otherwise empty list. """
		if self.verbose:
			return []
		return list(args)
	def verbose_arg(self, *args):
		""" Returns list of given args if verbose, otherwise empty list. """
		if self.quiet:
			return []
		return list(args)
	def debug(self, *args, **kwargs):
		""" Same as context.logger.debug() """
		return self._logger.debug(*args, **kwargs)
	def info(self, *args, **kwargs):
		""" Same as context.logger.info() """
		return self._logger.info(*args, **kwargs)
	def warning(self, *args, **kwargs):
		""" Same as context.logger.warning() """
		return self._logger.warning(*args, **kwargs)
	def error(self, *args, **kwargs):
		""" Same as context.logger.error() """
		return self._logger.error(*args, **kwargs)
	def critical(self, *args, **kwargs):
		""" Same as context.logger.critical() """
		return self._logger.critical(*args, **kwargs)
	def validate_worker_host(self, worker_name, caps_type=None, required_caps=None, current_caps=None):
		""" Checks if current host (with current caps) is acceptable for the job.
		Caps type can be a function that returns caps object.
		Caps object should be comparable and str-able.
		Minimum required caps can be specified.
		"""
		import socket
		current = WorkerStats(socket.gethostname(), current_caps, logger=self._logger)
		self._logger.debug('Current stats: {0}'.format(current))

		from clckwrkbdgr import xdg
		worker_host_file = xdg.save_state_path('dailyupdate')/'{0}.worker'.format(worker_name)
		stored = WorkerStats.load(worker_host_file, caps_type=caps_type, logger=self._logger)
		self._logger.debug('Stored stats: {0}'.format(stored))

		if not current.is_preferred(stored, required_caps):
			self._logger.debug('Current stats are not acceptable.')
			return False
		self._logger.debug('Current stats are acceptable.')
		current.save(worker_host_file)
		return True

def init(working_dir=None, verbose_var=None, logger_name=None, script_rootdir=None, only_platforms=None, skip_platforms=None): # pragma: no cover -- TODO need mocks
	""" Inits jobsequence context (see Context).
	If working_dir is specified, it is set as current directory.
	If verbose_var is specified, it will be used to check verbosity level for this jobsequence (e.g. DAILYUPDATE_VERBOSE).
	If only_platforms is specified, it should be string or list of strings that specify platform name.
	If current platform is not amongst specified, script will exit immediately.
	Same goes for skip_platforms, except logic is reversed.
	Also registers separate logger (default settings, output to console) with optional name.
	"""
	if working_dir:
		os.chdir(str(working_dir))
	import platform
	import six
	if only_platforms:
		if isinstance(only_platforms, six.string_types):
			only_platforms = [only_platforms]
		if platform.system().lower() not in map(str.lower, only_platforms):
			sys.exit()
	if skip_platforms:
		if isinstance(skip_platforms, six.string_types):
			skip_platforms = [skip_platforms]
		if platform.system().lower() in map(str.lower, skip_platforms):
			sys.exit()
	verbose_level = 0
	if verbose_var:
		verbose_level = len(os.environ.get(verbose_var, ''))
	return Context(
			verbose_level=verbose_level,
			logger_name=logger_name,
			script_rootdir=script_rootdir,
			)
