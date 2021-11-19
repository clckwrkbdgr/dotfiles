from __future__ import print_function, unicode_literals
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
import pyfakefs.fake_filesystem_unittest as fs_unittest
import os
import mimetypes
from .. import webserver

class MockPopen(object):
	def __init__(self, rc, stdout, stderr):
		self.rc = rc
		self.stdout = stdout
		self.stderr = stderr
	def communicate(self, stdin):
		return self.stdout, self.stderr
	def wait(self):
		return self.rc

class TestWebResponses(fs_unittest.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[webserver])
		self.fs.create_dir('/data')
	def should_prepare_base_response(self):
		response = webserver.Response(200, b'content', content_type='text/html', content_encoding='utf-8')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'content')
		self.assertEqual(response.get_headers(), {'Content-Type':'text/html', 'Content-Encoding':'utf-8'})
	def should_prepare_response_from_file(self):
		self.fs.create_file('/data/file.md', contents='content')
		response = webserver.FileContentResponse(200, '/data/file.md', content_type='text/html', content_encoding='utf-8')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'content')
		self.assertEqual(response.get_headers(), {'Content-Type':'text/html', 'Content-Encoding':'utf-8'})

		with open('/data/file.md', 'w') as f: f.write('content')
		response = webserver.FileContentResponse(200, '/data/file.md')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'content')
		expected_content_type, _ = mimetypes.guess_type('/data/file.md')
		self.assertEqual(response.get_headers(), {'Content-Type':expected_content_type or 'text/plain'})

		self.fs.create_file('/data/file.jpg', contents='content')
		response = webserver.FileContentResponse(200, '/data/file.jpg')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'content')
		self.assertEqual(response.get_headers(), {'Content-Type':'image/jpeg'})

		self.fs.create_file('/data/file.html', contents='<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head><body></body>')
		response = webserver.FileContentResponse(200, '/data/file.html')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head><body></body>')
		self.assertEqual(response.get_headers(), {'Content-Type':'text/html'})
	@mock.patch('subprocess.Popen', side_effect=[
		MockPopen(0, b'CONTENT' + os.linesep.encode(), b''),
		MockPopen(1, b'', b'ERROR'),
		])
	@mock.patch('clckwrkbdgr.webserver.base_log_message')
	def should_prepare_cgi_response(self, base_log_message, popen):
		self.fs.create_file('/data/file.md', contents='content')
		response = webserver.CGIResponse(200, '/data/file.md', 'python -c "import six; print(six.moves.input().upper())"')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'CONTENT' + os.linesep.encode())
		self.assertEqual(response.get_headers(), {'Content-Type':'text/html', 'Content-Encoding':'utf-8'})

		response = webserver.CGIResponse(200, '/data/file.md', 'unknown_command')
		self.assertEqual(response.get_code(), 200)
		self.assertEqual(response.get_content(), b'')
		self.assertEqual(response.get_headers(), {'Content-Type':'text/html', 'Content-Encoding':'utf-8'})
		base_log_message.assert_has_calls([
			mock.call('CGI process exited with %d', 1),
			mock.call('Error during processing CGI:\n%s', str(b'ERROR')),
			])
