from __future__ import print_function
import os, sys
import logging
import atexit

def _comply_about_accumulated_return_code(): # pragma: no cover
	if Context._global_return_code != 0:
		print('[jobsequence.context: Return code {0} was prepared but Context.done() was not called]'.format(Context._global_return_code), file=sys.stderr)
atexit.register(_comply_about_accumulated_return_code)

class Context: # pragma: no cover -- TODO need mocks
	_global_return_code = 0

	def __init__(self, verbose_level=None, logger_name=None):
		self._verbose_level = verbose_level

		self._logger = logging.getLogger(logger_name or 'jobsequence')
		if not self._logger.handlers:
			handler = logging.StreamHandler() # TODO custom formatter to display level, module, logger name etc.; and generic clckwrkbdgr module for such loggers.
			self._logger.addHandler(handler)
		if self._verbose_level == 1:
			self._logger.setLevel(logging.INFO)
		elif self._verbose_level > 1:
			self._logger.setLevel(logging.DEBUG)
		self._returncode = 0
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

def init(working_dir=None, verbose_var=None, logger_name=None, only_platforms=None, skip_platforms=None): # pragma: no cover -- TODO need mocks
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
			)
