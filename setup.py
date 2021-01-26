#!/usr/bin/env python
"""
Performs setup of dotfiles and some system options.

See '--help' for usage.
"""
import os
import click
import clckwrkbdgr.jobsequence as JB

dailyupdate = JB.JobSequence(
		verbose_var_name='DOTFILES_SETUP_VERBOSE',
		default_job_dir=os.path.join(os.environ['XDG_CONFIG_HOME'], 'setup.d'),
		click=click,
		)

if __name__ == '__main__':
	dailyupdate.cli()
