import os, sys, subprocess, logging
import itertools
from pathlib import Path, PurePath

CLI_USAGE = """
Job actions are defined as executable files (scripts, binaries) under job directory (see --dir option).

PATTERN is a plain-text part of the file to match job files. Job file will be executed if any of the patterns are found in its name.

Sequence of jobs is constructed from sorted list of job file names,
you may name them to control this order, e.g.:

  '00.first.job.sh', '01.second.job', '01.another.second.job' etc.

There are no specific requirements for name except for sorting order.

Job directory can be specified several times. In this case content of all directories is joined and sorted in total order.

Job executables are executed in the current environment with additional environment variable for verbosity level.

Default verbosity mode is 'fully quiet', each job is supposed to produce no output except for errors. It is up to the job executable how to interpret this verbosity level, e.g.: 'v' is normal output, 'vv' is detailed output and 'vvv' is debug level.

If verbosity level is >0, the main runner script will also print some info about executed actions.
"""

class JobSequence:
	def __init__(self, verbose_var_name, default_job_dir, click=None):
		self.verbose_var_name = verbose_var_name
		self.default_job_dirs = self._fix_job_dir_arg(default_job_dir)
		if click is None: # pragma: no cover
			import click
		self.click = click
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
	def patterns_argument(self):
		return self.click.argument('patterns', nargs=-1)
	def run(self, patterns, job_dirs, dry_run=False, verbose=0):
		job_dirs = self._fix_job_dir_arg(job_dirs)
		job_dirs = list(map(Path, job_dirs or self.default_job_dirs))
		if dry_run:
			verbose = max(1, verbose)
		if verbose:
			logging.getLogger().setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
		if not dry_run:
			os.environ[self.verbose_var_name] = 'v' * verbose
		else:
			logging.info("[DRY] {0}={1}".format(self.verbose_var_name, 'v' * verbose))
		logging.info("Verbosity level: {0}".format(verbose))
		logging.info("Searching in directories: {0}".format(job_dirs))
		total_rc = 0
		for entry in sorted(itertools.chain.from_iterable(job_dir.iterdir() for job_dir in job_dirs), key=lambda entry: entry.name):
			if patterns and all(pattern not in entry.name for pattern in patterns):
				logging.info("Job was not matched: {0}".format(entry))
				continue
			logging.info("Executing job: {0}".format(entry))
			if not dry_run:
				rc = subprocess.call([str(entry)], shell=True)
			else:
				logging.info("[DRY] Executing: `{0}`".format(entry))
				rc = 0
			logging.info("RC: {0}".format(rc))
			total_rc += rc
		return total_rc
	@property
	def cli(self):
		@self.click.command(epilog=CLI_USAGE)
		@self.verbose_option()
		@self.dry_run_option()
		@self.job_dir_option()
		@self.patterns_argument()
		def cli(patterns, job_dir=None, dry_run=False, verbose=0):
			""" Runs sequence of job actions.
			"""
			rc = self.run(patterns, job_dir, dry_run=dry_run, verbose=verbose)
			sys.exit(rc)
		return cli
