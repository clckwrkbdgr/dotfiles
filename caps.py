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

def list_attributes(filenames=None):
	if filenames:
		filenames = b'\n'.join(filename.encode('utf-8', 'replace') for filename in filenames)
	else:
		filenames = subprocess.check_output(['git', 'ls-files'])
	git = subprocess.Popen(['git', 'check-attr', '--stdin', 'caps'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	attrs, _ = git.communicate(filenames)
	git.wait()
	for line in attrs.split(b'\n'):
		if not line:
			continue
		filename, _, value = line.split(b': ')
		if not value or value == b'unspecified':
			value = None
		else:
			value = value.decode('utf-8', 'replace')
		try:
			filename = filename.decode()
		except:
			filename = repr(filename)
		yield filename, value

import click

@click.group()
def cli():
	if not Path('.git').is_dir():
		print('Should be executed from the root of Git repo.')
		sys.exit(1)

@cli.command('check')
@click.argument('filenames', nargs=-1, default=None)
def check_attributes(filenames):
	""" Checks attributes for given files or for all known to Git in current repo. """
	rc = 0
	for filename, value in list_attributes():
		if not value:
			print('Missing caps attribute: {0}'.format(filename))
			rc += 1
	sys.exit(rc)

@cli.command('list')
@click.argument('tag')
def list_files(tag):
	""" Lists files for given tag. """
	for filename, value in list_attributes():
		if value == tag:
			print(filename)

@cli.command('sparse')
@click.argument('tag')
def sparse_checkout(tag):
	""" Updates sparse-checkout list for given tag.
	Does not updates actual working tree! It has to be done manually afterwards, e.g. via `git checkout master` or `git read-tree -mu HEAD`.
	Exits with non-zero when work tree needs update.
	"""
	lines = [filename for filename, value in list_attributes() if value == tag]
	sparse_checkout = Path('.git')/'info'/'sparse-checkout'
	if lines == sparse_checkout.read_text().splitlines():
		sys.exit(0) # Already up-to-date.
	sparse_checkout.write_text('\n'.join(lines) + '\n')
	(Path('.git')/'info'/'CAPS').write_text(tag)
	sys.exit(1) # Worktree needs update.

if __name__ == '__main__':
	cli()
