import os, sys, subprocess, logging
import itertools
try:
	from pathlib2 import Path, PurePath
except ImportError: # pragma: no cover
	from pathlib import Path, PurePath
from .. import xdg
from .. import logging as clckwrkbdgr_logging

CLI_USAGE = """
Job actions are defined as executable files (scripts, binaries) under job directory (see --dir option).

PATTERN is a plain-text part of the file to match job files. Job file will be executed if any of the patterns are found in its name. Additionally, excluding patterns can be specified starting with symbols '!'. Job is skipped, if any of the exclude patterns is found in its name. Patterns can be combined, e.g.: [foo, bar, baz] => (ba, !baz) => [bar]

Sequence of jobs is constructed from sorted list of job file names,
you may name them to control this order, e.g.:

  '00.first.job.sh', '01.second.job', '01.another.second.job' etc.

There are no specific requirements for name except for sorting order.

Job directory can be specified several times. In this case content of all directories is joined and sorted in total order.

Job executables are executed in the current environment with additional environment variable for verbosity level.

Default verbosity mode is 'fully quiet', each job is supposed to produce no output except for errors. It is up to the job executable how to interpret this verbosity level, e.g.: 'v' is normal output, 'vv' is detailed output and 'vvv' is debug level.

If verbosity level is >0, the main runner script will also print some info about executed actions.
"""

def process_alive(pid): # pragma: no cover -- TODO to some OS-utils module.
	import platform
	if platform.system() == 'Windows':
		try:
			output = subprocess.check_output(["tasklist", "/FI", "PID eq {0}".format(pid)], stderr=subprocess.STDOUT)
			if str(pid).encode() in output:
				return True
		except subprocess.CalledProcessError:
			pass
	else:
		import os
		try:
			os.kill(pid, 0)
			return True
		except OSError:
			pass
		return False

def run_job_executable(executable, header=None): # pragma: no cover -- TODO processes and stdouts.
	"""
	Runs executable (using shell=True), checks for stdout/stderr.
	If there was any output, prints specified header before dumping streams.
	Header is printed w/o line feed, so it should be included in the header manually if needed.
	Returns pair (rc, was_output).
	"""
	header = header or (str(executable)+'\n')
	process = subprocess.Popen([str(executable)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # TODO maybe stdin=DEVNULL? As these jobs should always be automatically.
	stdout, stderr = process.communicate()
	if stdout or stderr:
		sys.stdout.write(header)
		sys.stdout.flush()
	was_output = b''
	if stdout:
		was_output += stdout
		if hasattr(sys.stdout, 'buffer'):
			sys.stdout.buffer.write(stdout)
		else:
			sys.stdout.write(stdout)
		sys.stdout.flush()
	if stderr:
		was_output += stderr
		if hasattr(sys.stderr, 'buffer'):
			sys.stderr.buffer.write(stderr)
		else:
			sys.stderr.write(stderr)
		sys.stderr.flush()
	rc = process.wait()
	return rc, was_output

class JobSequence:
	def __init__(self, verbose_var_name, default_job_dir, click=None, default_state_dir=None):
		self.verbose_var_name = verbose_var_name
		self.default_job_dirs = self._fix_job_dir_arg(default_job_dir)
		if not default_state_dir: # pragma: no cover
			import socket
			default_state_dir = xdg.save_state_path('jobsequence')/socket.gethostname()
		self.default_state_dir = default_state_dir
		if click is None: # pragma: no cover
			import click
		self.click = click
	def _is_unwanted(self, filepath):
		if filepath.name == '__pycache__':
			return True
		if filepath.suffix in ['.pyc']:
			return True
		return False
	def _fix_job_dir_arg(self, job_dir):
		if job_dir is None:
			return None
		if any(isinstance(job_dir, t) for t in [str, PurePath]):
			return [job_dir]
		return job_dir
	def verbose_option(self):
		return self.click.option('-v', '--verbose', count=True,
				help="Verbosity level."
				"Passed to jobs via ${varname}."
				"Has cumulative value, each flag adds one level to verbosity and one character to environment variable: {varname}=vvv.".format(
					varname=self.verbose_var_name,
					),
				)
	def dry_run_option(self):
		return self.click.option('--dry', 'dry_run', is_flag=True, help="Dry run. Only report about actions, do not actually execute them. Implies at least one level in verbosity.")
	def job_dir_option(self):
		return self.click.option('-d', '--dir', 'job_dirs', multiple=True, default=self.default_job_dirs, show_default=True, help="Custom directory with job files. Can be specified several times, job files from all directories are sorted and executed in total order.")
	def state_dir_option(self):
		return self.click.option('--state-dir', 'state_dir', default=self.default_state_dir, show_default=True, type=Path, help="Path to directory to store intermediate state of running jobsequence processes. Useful for investigation when the process takes a long time and terminated abnormally. Such remaining files will be reported when their process is not detected as alive.")
	def patterns_argument(self):
		return self.click.argument('patterns', nargs=-1)
	def save_state(self, state_file, data): # pragma: no cover -- TODO FS
		if not state_file:
			return
		import datetime
		with state_file.open('ab+') as f:
			f.write('!!! {0}\n'.format(datetime.datetime.now()).encode())
			f.write(data)
			f.write('\n\n'.encode())
	def run(self, patterns, job_dirs, dry_run=False, verbose=0, state_dir=None):
		state_file = None
		if state_dir and state_dir.exists(): # pragma: no cover -- TODO FS
			for entry in state_dir.iterdir():
				pid = int(entry.name)
				if not process_alive(pid):
					sys.stderr.write('!!! Jobsequence state file exists, but process is not alive: {0}\n'.format(entry))
					sys.stderr.flush()
			state_file = state_dir/str(os.getpid())

		job_dirs = self._fix_job_dir_arg(job_dirs)
		job_dirs = list(map(Path, job_dirs or self.default_job_dirs))
		if dry_run:
			verbose = max(1, verbose)
		logger = logging.getLogger('jobsequence')
		clckwrkbdgr_logging.init(
				logger, verbose=verbose,
				debug=(verbose is not None and verbose > 1),
				timestamps=(verbose is not None and verbose > 2),
				)
		if not dry_run:
			os.environ[self.verbose_var_name] = 'v' * verbose
		else:
			logger.info("[DRY] {0}={1}".format(self.verbose_var_name, 'v' * verbose))
		patterns = patterns or []
		include_patterns = [pattern for pattern in patterns if not pattern.startswith('!')]
		exclude_patterns = [pattern[1:] for pattern in patterns if pattern.startswith('!')]
		logger.info("Verbosity level: {0}".format(verbose))
		logger.info("Searching in directories: {0}".format(job_dirs))
		if include_patterns:
			logger.info("Including patterns: {0}".format(include_patterns))
		if exclude_patterns:
			logger.info("Excluding patterns: {0}".format(exclude_patterns))
		total_rc = 0
		entries = (
				job_dir.iterdir() if job_dir.is_dir() else []
				for job_dir
				in job_dirs
				)
		was_output = False
		main_title = Path(sys.modules['__main__'].__file__).name
		self.save_state(state_file, b'START\n')
		for entry in sorted(itertools.chain.from_iterable(entries), key=lambda entry: entry.name):
			if self._is_unwanted(entry):
				logger.info("Skipping unwanted entry: {0}".format(entry))
				continue
			if include_patterns and all(pattern not in entry.name for pattern in include_patterns):
				logger.info("Job was not matched by include patterns: {0}".format(entry))
				continue
			if exclude_patterns and any(pattern in entry.name for pattern in exclude_patterns):
				logger.info("Job was unmatched by exclude patterns: {0}".format(entry))
				continue
			self.save_state(state_file, str(entry).encode('ascii', 'replace') + b'\n')
			logger.info("Executing job: {0}".format(entry))
			if not dry_run:
				header = '=== {0} : {1}\n'.format(main_title, str(entry))
				rc, job_has_output = run_job_executable(entry, header)
				self.save_state(state_file, job_has_output)
				was_output = was_output or job_has_output
			else:
				logger.info("[DRY] Executing: `{0}`".format(entry))
				rc = 0
			logger.info("RC: {0}".format(rc))
			total_rc += rc
		if was_output: # pragma: no cover -- TODO
			sys.stdout.write('=== {0} : [Finished]\n'.format(main_title))
			sys.stdout.flush()
		if state_file: # pragma: no cover -- TODO FS
			os.unlink(str(state_file))
		return total_rc
	@property
	def cli(self):
		@self.click.command(epilog=CLI_USAGE)
		@self.verbose_option()
		@self.dry_run_option()
		@self.job_dir_option()
		@self.state_dir_option()
		@self.patterns_argument()
		def cli(patterns, job_dirs=None, dry_run=False, verbose=0, state_dir=None):
			""" Runs sequence of job actions.
			"""
			rc = self.run(patterns, job_dirs, dry_run=dry_run, verbose=verbose, state_dir=state_dir)
			sys.exit(rc)
		return cli
