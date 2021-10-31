#!/usr/bin/env python
""" Manages dotfiles repo capabilities.
Each file should have git attribute "caps=...", where value is some tag name.
It will allow to setup sparse checkout for specific purposes using those tags.
"""
import sys, subprocess
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
import clckwrkbdgr.vcs.git as git

import click

@click.group()
def cli():
	if not git.is_repo_root():
		print('Should be executed from the root of Git repo.')
		sys.exit(1)

@cli.command('check')
@click.argument('filenames', nargs=-1, default=None)
def check_attributes(filenames):
	""" Checks attributes for given files or for all known to Git in current repo. """
	rc = 0
	for filename, value in git.list_attributes('caps'):
		if not value:
			print('Missing caps attribute: {0}'.format(filename))
			rc += 1
	sys.exit(rc)

@cli.command('list')
@click.argument('tag')
def list_files(tag):
	""" Lists files for given tag. """
	for filename, value in git.list_attributes('caps'):
		if value == tag:
			print(filename)

@cli.command('sparse')
@click.argument('tag')
def sparse_checkout(tag):
	""" Updates sparse-checkout list for given tag.
	Does not updates actual working tree! It has to be done manually afterwards, e.g. via `git checkout master` or `git read-tree -mu HEAD`.
	Exits with non-zero when work tree needs update.
	"""
	lines = [filename for filename, value in git.list_attributes('caps') if value == tag]
	sparse_checkout = git.SparseCheckout()
	if lines == sparse_checkout.lines():
		sys.exit(0) # Already up-to-date.
	sparse_checkout.update_with('\n'.join(lines) + '\n')
	(Path('.git')/'info'/'CAPS').write_text(tag)
	sys.exit(1) # Worktree needs update.

if __name__ == '__main__':
	cli()
