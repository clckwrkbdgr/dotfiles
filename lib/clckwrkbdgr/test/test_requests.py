import sys
from .. import unittest
from .. import requests

urllib_urlopen_name = {
	2: 'urllib2.urlopen',
	3: 'urllib.request.urlopen',
	}[sys.version_info[0]]

class MockUrllibResponse(object):
	def __init__(self, data):
		self.data = data
	def read(self):
		return self.data

class TestResponse(unittest.TestCase):
	def should_access_raw_binary_data(self):
		response = requests.Response(b'data')
		self.assertEqual(response.data, b'data')
		self.assertEqual(response.as_binary(), b'data')

class TestGetRequest(unittest.TestCase):
	@unittest.mock.patch(urllib_urlopen_name)
	def should_perform_get_request(self, urllib_urlopen):
		urllib_urlopen.return_value = MockUrllibResponse(b'data')
		response = requests.get('http://localhost/path')
		self.assertEqual(response.data, b'data')
		urllib_urlopen.assert_called_with('http://localhost/path', timeout=30)
	@unittest.mock.patch(urllib_urlopen_name)
	def should_perform_get_request_with_timeout(self, urllib_urlopen):
		urllib_urlopen.return_value = MockUrllibResponse(b'data')
		response = requests.get('http://localhost/path', timeout=1)
		self.assertEqual(response.data, b'data')
		urllib_urlopen.assert_called_with('http://localhost/path', timeout=1)
