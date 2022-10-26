import sys, platform, subprocess
import itertools
import re
try:
	import configparser
except ImportError: # pragma: no cover
	import ConfigParser as configparser
from . import runner

PYTHON_UNITTEST_QUIET_PATTERNS = {
		'2' : list(map(re.compile, [
			'^[.s]+$',
			'^-{70}$',
			r'^Ran \d+ tests? in [0-9.]+s$',
			'^$',
			r'^OK( \(skipped=\d+\))?$',
			])),
		'3' : list(map(re.compile, [
			'^-{70}$',
			r'^Ran \d+ tests? in [0-9.]+s$',
			'^$',
			r'^OK( \(skipped=\d+\))?$',
			])),
		}
PYTHON_COVERAGE_QUIET_PATTERNS = list(map(re.compile, [
	'^Name +Stmts +Miss +Cover +Missing$',
	'^-{37}$',
	'^-{37}$',
	'^TOTAL +[0-9]+ +0 +100%$',
	'^$',
	'^.*due to complete coverage[.]$'
	]))

def quiet_call(args,
		quiet_stdout_patterns=None, quiet_stderr_patterns=None,
		exclude_stdout_patterns=None, exclude_stderr_patterns=None,
		): # pragma: no cover -- TODO
	process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate(None)
	rc = process.wait()
	buffers_to_check = [
			(stdout, quiet_stdout_patterns, exclude_stdout_patterns, sys.stdout),
			(stderr, quiet_stderr_patterns, exclude_stderr_patterns, sys.stderr),
			]
	for buffer, patterns, exclude_patterns, stream in buffers_to_check:
		if hasattr(stream, 'buffer'):
			stream = stream.buffer
		if buffer and exclude_patterns:
			lines = buffer.decode('utf-8', 'replace').splitlines()
			lines = [line for line in lines
					if not any(pattern.match(line) for pattern in exclude_patterns)
					]
			buffer = ('\n'.join(lines) + '\n').encode('utf-8', 'replace')
		do_print = True
		if buffer and patterns:
			lines = buffer.decode('utf-8', 'replace').splitlines()
			if len(lines) == len(patterns):
				if all(pattern.match(line) for line, pattern in zip(lines, patterns)):
					do_print = False
		if buffer and do_print:
			stream.write(buffer)
	sys.stdout.flush()
	sys.stderr.flush()
	return rc

def run_python_unittests(version, test, quiet=False): # pragma: no cover -- TODO
	allowed_versions = ['2', '3']
	assert version in allowed_versions, 'Unknown python version {0}, choose from following: {1}'.format(version, allowed_versions)

	setup_cfg = configparser.ConfigParser()
	setup_cfg.read(['setup.cfg'])
	custom_omit = []
	custom_coverage_run_category = 'coverage:run:py{0}'.format(version)
	if setup_cfg.has_section(custom_coverage_run_category):
		if setup_cfg.has_option(custom_coverage_run_category, 'omit'):
			custom_omit.extend(setup_cfg.get(custom_coverage_run_category, 'omit').splitlines())

	if platform.system() == 'Windows':
		python_runner = ['py', '-{0}'.format(version)]
		rc = subprocess.call(python_runner + ['-V'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		if rc == 103:
			if not quiet:
				print('Python {0} not found!'.format(version))
			return 0
	else:
		python_runner = ['python{0}'.format(version)]
		try:
			subprocess.call(python_runner + ['-V'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		except OSError:
			if not quiet:
				print('Python {0} not found!'.format(version))
			return 0

	args = python_runner + ['-m', 'coverage', 'run']
	if not test:
		args += ['--source=.']
	args += ['-m', 'unittest']
	if test:
		if quiet:
			args += ['--quiet']
		args += [test]
	else:
		args += ['discover']
		if version == '3' and quiet: # FIXME py2 discover does not recognize --quiet.
			args += ['--quiet']
	quiet_stderr_patterns = []
	if quiet:
		quiet_stderr_patterns.extend(PYTHON_UNITTEST_QUIET_PATTERNS[version])

	rc = quiet_call(args,
			quiet_stderr_patterns=quiet_stderr_patterns,
			)
	if rc != 0:
		return rc
	args = python_runner + ['-m', 'coverage', 'report', '-m']
	if custom_omit:
		args.extend(itertools.chain.from_iterable(
			('--omit', entry) for entry in custom_omit
			))
	return quiet_call(args,
			quiet_stdout_patterns=PYTHON_COVERAGE_QUIET_PATTERNS if quiet else None)

@runner.test_suite('py2')
def python_2_unittest(test, quiet=False): # pragma: no cover -- TODO
	return run_python_unittests('2', test, quiet=quiet)

@runner.test_suite('py3')
def python_3_unittest(test, quiet=False): # pragma: no cover -- TODO
	return run_python_unittests('3', test, quiet=quiet)
