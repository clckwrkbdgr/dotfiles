from __future__ import absolute_import
import logging

def getFileLogger(name, filename): # pragma: no cover
	logger = logging.getLogger(name)
	logger.addHandler(logging.FileHandler(str(filename), delay=True))
	return logger
