from __future__ import print_function
import os, sys
import subprocess
try:
	import SimpleHTTPServer
except ImportError: # pragma: no cover
	import http.server as SimpleHTTPServer
try:
	import SocketServer
except ImportError: # pragma: no cover
	import socketserver as SocketServer
try:
	from pathlib2 import Path, PurePosixPath
except ImportError: # pragma: no cover
	from pathlib import Path, PurePosixPath
import posixpath
import itertools
try:
	import html
except ImportError: # pragma: no cover -- py2 only
	import cgi as html
import mimetypes
import webbrowser
import six

def base_log_message(message, *args): # pragma: no cover
	print(message % tuple(args), file=sys.stderr)

class Response:
	def __init__(self, code, content, content_type='text/plain', content_encoding=None):
		self.code = code
		self.content = content
		self.content_type = content_type
		self.content_encoding = content_encoding
	def get_code(self):
		return self.code
	def get_content(self):
		return self.content
	def get_headers(self):
		headers = {}
		headers['Content-Type'] = self.content_type
		if self.content_encoding:
			headers['Content-Encoding'] = self.content_encoding
		return headers

class FileContentResponse(Response):
	def __init__(self, code, filename, content_type=None, content_encoding=None):
		self.code = code
		self.content = Path(filename).read_bytes()
		self.content_type, self.content_encoding = content_type, content_encoding
		if self.content_type is None:
			self.content_type, self.content_encoding = mimetypes.guess_type(str(filename))
		if self.content_type is None: # pragma: no cover
			self.content_type = 'text/plain'

class CGIResponse(Response):
	def __init__(self, code, filename, handler):
		self.code = code
		self.filename = filename
		self.content_encoding = 'utf-8'
		self.content = Path(filename).read_bytes()
		try:
			process = subprocess.Popen(handler, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			self.content, stderr = process.communicate(self.content)
			rc = process.wait()
			if rc != 0:
				base_log_message("CGI process exited with %d", rc)
			if stderr:
				base_log_message("Error during processing CGI:\n%s", str(stderr))
			self.content_type = 'text/html'
		except Exception as e: # pragma: no cover -- should never trigger as Popen has shell=True
			self.content = str(e)
			self.content_type = 'text/plain'
			self.code = 500

class MyHTTPHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	def log_message(self, message, *args): # pragma: no cover
		return base_log_message(message, *args)
	def _respond(self, response): # pragma: no cover
		content = response.get_content()
		headers = response.get_headers()
		if not isinstance(content, bytes):
			if 'Content-Encoding' not in headers:
				headers['Content-Encoding'] = 'utf-8'
			content = content.encode(headers['Content-Encoding'], 'replace')

		self.send_response(response.get_code())
		for header, value in headers.items():
			self.send_header(header, value)
		self.end_headers()
		try:
			self.wfile.write(content)
		except Exception as e:
			self.log_error(str(e))
	def mod_file_response(self, code, filename): # pragma: no cover
		for handler in self.server.config.handlers:
			if os.path.splitext(filename)[1].strip('.') == handler:
				return CGIResponse(code, filename, self.server.config.handlers[handler])
		return FileContentResponse(code, filename)
	def serve_filesystem(self, full_path): # pragma: no cover
		if os.path.isdir(full_path):
			content = '<html><head><title>{title}</title><meta http-equiv="content-type" content="text/html; charset=utf-8"/></head><body><h1>{title}</h1>'.format(title=html.escape(self.path))
			content += '<a href="{path}">..</a><br />'.format(path=html.escape(posixpath.join(self.path, '..')))
			for entry in os.listdir(full_path):
				if entry in self.server.config.exclude:
					continue
				isdir = ''
				if os.path.isdir(os.path.join(full_path, entry)):
					isdir = '/'
				content += '<a href="{path}">{entry}{isdir}</a><br />'.format(path=html.escape(posixpath.join(self.path, entry)), entry=html.escape(entry), isdir=isdir)
			content += '</body></html>'

			response = Response(200, content)
			response.content_type = 'text/html'
			self._respond(response)
		else:
			self._respond(self.mod_file_response(200, full_path))
	def do_GET(self): # pragma: no cover
		path = self.path
		if path.startswith('/'):
			path = path[1:]
		path_parts = list(map(six.moves.urllib.parse.unquote, PurePosixPath(path).parts))
		full_path = self.server.config.root
		if path_parts:
			full_path = os.path.join(full_path, os.path.join(*path_parts))
		if os.path.isfile(full_path):
			self._respond(self.mod_file_response(200, full_path))
		elif os.path.isdir(full_path):
			self.serve_filesystem(full_path)
		else:
			self._respond(Response(404, 'Not Found'))

class WebServer(object):
	def __init__(self, root='.', port=8080, exclude=None, handlers=None): # pragma: no cover
		self.server = None
		self.root = root
		self.port = port
		self.exclude = exclude or []
		self.handlers = handlers or dict()
	def stop(self): # pragma: no cover
		self.server.shutdown()
	def run(self): # pragma: no cover
		self.server = SocketServer.TCPServer(("", self.port), MyHTTPHandler)
		self.server.config = self
		base_log_message("serving at port %d", self.port)
		base_log_message("Kill with Ctrl-C")
		try:
			self.server.serve_forever()
		except KeyboardInterrupt:
			base_log_message("Interrupted")

import click

@click.command()
@click.option("--open", is_flag=True,
		help='Open webbrowser with http://localhost:<port>/ after start.')
@click.option("--root", default='.',
		help='Root directory to server. Default is current.')
@click.option("--port", type=int, default=8080,
		help='Web server port to bind to. Default is 8080.')
@click.option("--exclude", multiple=True,
		help='Exclude specified files from the directory listings.')
@click.option("--handler", multiple=True,
		help="List of CGI handlers (stdin->stdout). Format is '<extension>=<command>'."
		"CGI command should produce valid UTF-8 HTML without headers.")
def cli(open=False, root='.', port=8080, exclude=None, handler=None): # pragma: no cover
	root = os.path.abspath(root)
	exclude = exclude or []
	handler = dict(value.split('=', 1) for value in handler or [])
	if open:
		import threading
		browser_thread = threading.Thread(target=lambda:webbrowser.open("http://localhost:{0}/".format(port)))
		browser_thread.start()
	WebServer(root, port, exclude=exclude, handlers=handler).run()

if __name__ == "__main__": # pragma: no cover
	cli()
