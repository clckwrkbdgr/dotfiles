import os, subprocess, platform
import time
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
from . import runner

@runner.test_suite('html')
def html_javascript_unittest(test, quiet=False): # pragma: no cover -- TODO
	import bottle

	rootpath = Path()
	@bottle.route('/lib/<javascript_module>.js')
	def host_dotfiles_js_library(javascript_module):
		bottle.response.content_type = 'application/javascript'
		return (rootpath/'{0}.js'.format(javascript_module)).read_text()
	@bottle.route('/lib/test/test_<javascript_module>.html')
	def host_dotfiles_js_library(javascript_module):
		return (rootpath/'test'/'test_{0}.html'.format(javascript_module)).read_text()

	from blackcompany.util.adhocserver import AdhocBackgroundServer
	# Unit testing pages require cookies, so if cookies are disabled by default,
	# then each random port will require a separate permission - which is bothersome.
	# So here's the option to pick 'random' port manually.
	custom_port = os.environ.get('CLCKWRKBDGR_UNITTEST_HTML_PORT')
	with AdhocBackgroundServer(port=custom_port) as server:
		found_tests = discover_tests('.', test=test)
		rc = run_tests(found_tests, port=server.port)
		time.sleep(5) # FIXME: waits until test pages are loaded in browser, but actually should received proper test results from the page and only then shut server down.
	return rc

def discover_tests(rootpath, test=None): # pragma: no cover -- TODO
	found_tests = []
	for root, dirnames, filenames in os.walk(str(rootpath)):
		for filename in filenames:
			if filename.startswith('test_') and filename.endswith('.html'):
				if test:
					print(test, filename)
					if filename == test or os.path.splitext(filename)[0] == test:
						found_tests.append(os.path.join(root, filename))
				else:
					found_tests.append(os.path.join(root, filename))
	return found_tests

def run_tests(found_tests, port): # pragma: no cover -- TODO
	if not found_tests:
		return 0
	command = ['firefox', '--hide']
	command += ['http://localhost:{0}/lib/{1}?close-on-success=true'.format(port, test_file) for test_file in found_tests]
	rc = subprocess.call(command, shell=(platform.system()=='Windows'))
	return rc
