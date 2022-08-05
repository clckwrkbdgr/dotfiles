import os, subprocess, platform
from . import runner

@runner.test_suite('html')
def html_javascript_unittest(test, quiet=False): # pragma: no cover -- TODO
	found_tests = []
	for root, dirnames, filenames in os.walk('.'):
		for filename in filenames:
			if filename.startswith('test_') and filename.endswith('.html'):
				if test:
					print(test, filename)
					if filename == test or os.path.splitext(filename)[0] == test:
						found_tests.append(os.path.join(root, filename))
				else:
					found_tests.append(os.path.join(root, filename))
	if not found_tests:
		return 0
	command = ['firefox', '--hide']
	command += ['http://localhost:20113/lib/{0}?close-on-success=true'.format(test_file) for test_file in found_tests]
	rc = subprocess.call(command, shell=(platform.system()=='Windows'))
	return rc
