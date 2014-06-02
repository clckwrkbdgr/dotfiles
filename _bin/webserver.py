#!/usr/bin/python3
import os
import sys
import subprocess
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler

class RequestHandler(BaseHTTPRequestHandler):
	def do_HEAD(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

	def do_GET(self):
		try:
			if self.path == '/':
				#self.path = '/wiki.py?search=Home'
				self.path = '/index.py'
				#self.path = '/index.html'

			param_str = ''
			if '?' in self.path:
				self.path, param_str = self.path.split('?', 1)

			message = None
			content_type = 'text/html'

			if self.path.endswith('.py'):
				try:
					message = subprocess.check_output(["python3", self.path.lstrip('/'), param_str], stderr=subprocess.STDOUT)
				except subprocess.CalledProcessError as e:
					message = '{0} returned with code {1}\n{2}'.format(e.cmd, e.returncode, e.output).encode('utf-8')
			else:
				file_path = os.curdir + os.sep + self.path
				f = open(file_path, "rb")
				message = f.read()
				f.close()

				file_mimetype, file_encoding = mimetypes.guess_type(file_path)
				if file_mimetype:
					content_type = file_mimetype

			self.send_response(200)
			self.send_header('Content-type', content_type)
			self.end_headers()
			if message:
				self.wfile.write(message)
		except IOError:
			self.send_error(404, 'File Not Found: %s' % self.path)

if __name__ == "__main__":
	port = 8000
	if len(sys.argv) > 1:
		port = int(sys.argv[1])

	try:
		server = HTTPServer( ('', port), RequestHandler)
		print('Starting web server...')
		print('Press ^C once or twice to quit.')
		server.serve_forever()
	except KeyboardInterrupt:
		print('^C received, shutting down server')
		server.socket.close()
