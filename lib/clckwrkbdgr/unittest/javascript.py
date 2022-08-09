from __future__ import print_function
import os, sys, subprocess, platform
import json
import time
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
from . import runner

@runner.test_suite('html')
def html_javascript_unittest(test, quiet=False): # pragma: no cover -- TODO
	try:
		from blackcompany.util.adhocserver import AdhocBackgroundServer
	except ImportError:
		if not quiet:
			print('Cannot import blackcompany.util.adhocserver, skipping tests.', file=sys.stderr)
		return 0
	try:
		import bottle
	except ImportError:
		if not quiet:
			print('Cannot import bottle, skipping tests.', file=sys.stderr)
		return 0

	found_tests = discover_tests('.', test=test)
	if not found_tests:
		return 0

	rootpath = Path()
	unittest_results = {}

	@bottle.route('/lib/<javascript_module>.js')
	def serve_js_library(javascript_module):
		bottle.response.content_type = 'application/javascript'
		return (rootpath/'{0}.js'.format(javascript_module)).read_text()
	@bottle.route('/lib/test/test_<javascript_module>.html')
	def serve_js_test_pages(javascript_module):
		return (rootpath/'test'/'test_{0}.html'.format(javascript_module)).read_text()
	@bottle.post('/lib/test/test_<javascript_module>.html')
	def accept_testing_results(javascript_module):
		data = bottle.request.body.read().decode('utf-8', 'replace')
		data = json.loads(data)
		unittest_results[javascript_module] = data
		if not quiet:
			print('=== {0}:'.format(javascript_module))
		successful, failed = 0, 0
		for test_name in data['results']:
			if data['results'][test_name]:
				if not quiet:
					print('OK: {0}'.format(test_name))
				successful += 1
			else:
				print('FAILED: {0}'.format(test_name))
				print(data['errors'][test_name])
				failed += 1
		if not quiet:
			if successful:
				print('Successful tests: {0}'.format(successful))
			if failed:
				print('Failed tests: {0}'.format(failed))

	# Unit testing pages require cookies, so if cookies are disabled by default,
	# then each random port will require a separate permission - which is bothersome.
	# So here's the option to pick 'random' port manually.
	custom_port = os.environ.get('CLCKWRKBDGR_UNITTEST_HTML_PORT')
	with AdhocBackgroundServer(port=custom_port) as server:
		rc = run_tests(found_tests, port=server.port)
		# Wait until all unit test pages execute and return results.
		for _ in range(10000):
			time.sleep(0.1)
			if len(unittest_results) == len(found_tests):
				break
	rc += sum(len(module['errors']) for module in unittest_results.values())
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
