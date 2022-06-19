#!/usr/bin/env python
"""
Performs setup of dotfiles and some system options.

See '--help' for usage.
"""
import os
from collections import OrderedDict
import click
import clckwrkbdgr.jobsequence as JB

setup = JB.JobSequence(
		verbose_var_name='DOTFILES_SETUP_VERBOSE',
		default_job_dir=list(OrderedDict.fromkeys((
			os.path.join(os.environ['XDG_CONFIG_HOME'], 'setup.d'),
			os.path.join(os.environ['XDG_DATA_HOME'], 'setup.d'),
			os.path.join(os.environ['HOME'], '.local', 'setup.d'),
			os.path.join(os.environ['HOME'], '.local', 'share', 'setup.d'),
			))),
		click=click,
		)

if __name__ == '__main__':
	setup.cli()
