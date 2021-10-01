from __future__ import absolute_import
from time import *
import datetime
import six

def get_utctimestamp(mtime=None): # pragma: no cover
	""" Converts local mtime (timestamp) to integer UTC timestamp.
	If mtime is None, returns current UTC time.
	"""
	if mtime is None:
		if six.PY2:
			return int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())
		return int(datetime.datetime.utcnow().timestamp())
	return int(calendar.timegm(datetime.datetime.fromtimestamp(mtime).timetuple()))

