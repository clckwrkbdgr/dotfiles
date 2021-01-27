import os, sys, subprocess, logging

CLI_USAGE = """
Job actions are defined as executable files (scripts, binaries) under job directory (see --dir option).

PATTERN is a plain-text part of the file to match job files. Job file will be executed if any of the patterns are found in its name.

Sequence of jobs is constructed from sorted list of job file names,
you may name them to control this order, e.g.:

  '00.first.job.sh', '01.second.job', '01.another.second.job' etc.

There are no specific requirements for name except for sorting order.

Job executables are executed in the current environment with additional environment variable for verbosity level.

Default verbosity mode is 'fully quiet', each job is supposed to produce no output except for errors. It is up to the job executable how to interpret this verbosity level, e.g.: 'v' is normal output, 'vv' is detailed output and 'vvv' is debug level.

If verbosity level is >0, the main runner script will also print some info about executed actions.
"""

class JobSequence:
	def __init__(self, verbose_var_name, default_job_dir, click=None):
		self.verbose_var_name = verbose_var_name
		self.default_job_dir = default_job_dir
		if click is None: # pragma: no cover
			import click
		self.click = click
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
		return self.click.option('-d', '--dir', 'job_dir', default=self.default_job_dir, show_default=True, help="Custom directory with job files.")
	def patterns_argument(self):
		return self.click.argument('patterns', nargs=-1)
	def run(self, patterns, job_dir, dry_run=False, verbose=0):
		job_dir = job_dir or self.default_job_dir
		if dry_run:
			verbose = max(1, verbose)
		if verbose:
			logging.getLogger().setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
		if not dry_run:
			os.environ[self.verbose_var_name] = 'v' * verbose
		else:
			logging.info("[DRY] {0}={1}".format(self.verbose_var_name, 'v' * verbose))
		logging.info("Verbosity level: {0}".format(verbose))
		logging.info("Searching in directory: {0}".format(job_dir))
		total_rc = 0
		for entry in sorted(os.listdir(job_dir)):
			if patterns and all(pattern not in entry for pattern in patterns):
				logging.info("Job was not matched: {0}".format(entry))
				continue
			logging.info("Executing job: {0}".format(entry))
			if not dry_run:
				rc = subprocess.call([os.path.join(job_dir, entry)], shell=True)
			else:
				logging.info("[DRY] Executing: `{0}`".format(os.path.join(job_dir, entry)))
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
