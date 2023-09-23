import blackcompany.concurrent
import blackcompany
import blackcompany.serve
import os, sys

# Hiding BrokenPipeError stacks from log.
# TODO: should be replaced by more robust WSGI server, e.g. CherryPy.
from wsgiref.handlers import BaseHandler
import sys
def ignore_broken_pipes(self): 
	if sys.exc_info()[0] != BrokenPipeError: BaseHandler.__handle_error_original_(self)
BaseHandler.__handle_error_original_ = BaseHandler.handle_error
BaseHandler.handle_error = ignore_broken_pipes

badger_web_root = os.environ.get('BADGER_WEB_ROOT')
if badger_web_root and os.path.isdir(badger_web_root):
	blackcompany.serve.plugin.discover(badger_web_root)
blackcompany.serve.plugin.discover(os.path.join(os.path.dirname(__file__), 'dotfiles'))

if __name__ == '__main__':
	if sys.argv[1:] == ['test']:
		# Main page for test server with some shortcut links for testing.
		import bottle
		@bottle.route('/')
		def _main_test_page(): # TODO: should be performed using blackcompany functionality.
			# TODO should retrieve this list from the module itself,
			# TODO using some kind of registry or plugin system
			# TODO and passing it through loaded modules.
			# TODO and also the template.
			result = ""
			rootdir = os.path.realpath(__file__)
			dotfiles_rootdir = os.path.dirname(os.path.dirname(rootdir))
			for test_html in os.listdir(os.path.join(dotfiles_rootdir, 'lib', 'test')):
				if test_html.startswith('test_') and test_html.endswith('.html'):
					result += "<p><a href='/lib/test/{0}'>{0}</a></p>".format(test_html)
			return result
		# Hack: waiting for server to start before opening page.
		import threading, webbrowser
		threading.Timer(1.0, lambda: webbrowser.open('http://localhost:2113/')).start()

		del sys.argv[1]
		blackcompany.run_cli(host='127.0.0.1', port=2113) # 2113 == ZNE
	else:
		blackcompany.run_cli(host='0.0.0.0', port=20113) # 20113 == ZONE
