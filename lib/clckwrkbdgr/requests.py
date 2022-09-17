import sys
try:
	import urllib.request
except: # pragma: no cover
	import urllib2

class Response(object):
	""" Result of remote request.
	"""
	def __init__(self, data):
		self._data = data
	@property
	def data(self):
		""" Provides access to raw binary data. """
		return self._data
	def as_binary(self):
		""" Returns raw binary data.
		Equivalent to <response>.data
		"""
		return self._data

def get(url, timeout=30):
	""" Performs GET request.
	Returns Response object.
	"""
	if sys.version_info[0] == 2: # pragma: no cover
		urlopen = urllib2.urlopen
	else: # pragma: no cover
		urlopen = urllib.request.urlopen
	request = urlopen(url, timeout=timeout)
	response = Response(request.read())
	return response
