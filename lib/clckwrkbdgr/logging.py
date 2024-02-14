from __future__ import absolute_import
import sys
import logging
import vintage

@vintage.deprecated('Use clckwrkbdgr.logging.init() instead.')
def getFileLogger(name, filename): # pragma: no cover
	return init(name, filename=filename, stream=None)

def init(logger,
		debug=False, verbose=False,
		timestamps=False,
		filename=None, stream=sys.stderr,
		rewrite_file=False,
		):
	""" Creates and initializes specified logger (logging.Logger object or name).

	If verbose is True, sets INFO level. Default level is WARNING.
	If debug is True, sets DEBUG level. Parameter verbose is ignored in this case.

	By default writes to stderr. Stream could be specified or set to None.
	If filename is given, duplicates output to the given file.
	If rewrite_file is True, file is cleared. Otherwise new log entries will be appened to the existing file (default mode).

	Uses following formats:
	- stream: [<LEVEL>] <logger name>:<message>
	- file: <time>:<logger name>:<LEVEL>:<message>

	If timestamps is True, then stream logger also will have timestamps.

	Returns created logger. Logger can also be accessed later using logging.getLogger(name)
	Returned logger will be callable, direct call will be equivalent to calling logging function corresponding to minimal logging level (e.g. logger.debug, logger.warning etc).

	Also, if root logger wasn't initialized, calls logging.basicConfig with the same parameters.
	"""
	if isinstance(logger, str):
		logger = logging.getLogger(logger)

	if logger.handlers:
		for _handler in logger.handlers[:]:
			logger.removeHandler(_handler)
	logger.propagate = False

	level = logging.WARNING
	if debug:
		level = logging.DEBUG
	elif verbose:
		level = logging.INFO

	loggers = [logger]
	if not logging.getLogger().handlers:
		logging.basicConfig()
		for _handler in logging.root.handlers[:]: # We will use custom logger instead of the stock one.
			logging.root.removeHandler(_handler)
		loggers.append(logging.getLogger())

	for logger_obj in loggers:
		if stream:
			stream_handler = logging.StreamHandler(stream)
			fmt_string = '[%(levelname)s] %(name)s: %(message)s'
			if timestamps:
				fmt_string = '%(asctime)s ' + fmt_string
			stream_handler.setFormatter(logging.Formatter(fmt_string,
				datefmt='%Y-%m-%d %H:%M:%S',
				))
			logger_obj.addHandler(stream_handler)
			# TODO colors
			# TODO DEBUG logging.basicConfig(format='%(module)s:%(lineno)d:%(funcName)s:%(levelname)s:%(message)s')
			# TODO DEBUG _handler.setFormatter(logging.Formatter('%(process)d: %(asctime)s: %(module)s:%(lineno)d:%(funcName)s: [%(levelname)s] %(message)s'))
		if filename:
			file_handler = logging.FileHandler(str(filename), delay=True, encoding='utf-8',
								  mode='w' if rewrite_file else 'a',
								  )
			file_handler.setFormatter(logging.Formatter(
				'%(asctime)s:%(name)s:%(levelname)s: %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S',
				))
			logger_obj.addHandler(file_handler)
		logger_obj.setLevel(level)

	logger.__call__ = lambda *args, **kwargs: logger.log(level, *args, **kwargs)

	return logger
