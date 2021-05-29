import os
import logging

class Context: # pragma: no cover -- TODO need mocks
	def __init__(self, verbose_level=None, logger_name='jobsequence'):
		self._verbose_level = verbose_level

		self._logger = logging.getLogger(logger_name)
		if not self._logger.handlers:
			handler = logging.StreamHandler() # TODO custom formatter to display level, module, logger name etc.; and generic clckwrkbdgr module for such loggers.
			self._logger.addHandler(handler)
		if self._verbose_level == 1:
			self._logger.setLevel(logging.INFO)
		elif self._verbose_level > 1:
			self._logger.setLevel(logging.DEBUG)
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
		verbose_var = len(os.environ.get(verbose_var, ''))
	return Context(
			verbose_level=verbose_level,
			logger_name=logger_name,
			)
