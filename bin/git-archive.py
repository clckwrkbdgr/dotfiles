#!/usr/bin/env python
"""
Utility to create/fetch git repos as plain archive on systems where git is not available.

Works for Py2/Py3, Windows/Unix. No external dependencies. Only batteries are required.
"""
import os, sys, subprocess
import posixpath, fnmatch
import logging
from clckwrkbdgr import requests

def update_sparse_checkout_attributes(attributes, export_ignore_files):
	EXPORT_IGNORE_BEGIN, EXPORT_IGNORE_END = '##{ SPARSE_CHECKOUT', '##} SPARSE_CHECKOUT'
	export_ignore = [EXPORT_IGNORE_BEGIN] + [
			line.replace(' ', '[[:space:]]') + ' export-ignore'
			for line
			in export_ignore_files
			] + [EXPORT_IGNORE_END]
	if not os.path.exists(attributes):
		content = export_ignore
	else:
		content = []
		in_export_ignore = False
		found_export_ignore = False
		with open(attributes, 'rb') as f:
			data = f.read()
		for line in data.decode('utf-8').splitlines():
			if line == EXPORT_IGNORE_BEGIN:
				in_export_ignore = True
				found_export_ignore = True
				content.extend(export_ignore)
			elif line == EXPORT_IGNORE_END:
				in_export_ignore = False
			elif in_export_ignore:
				pass
			else:
				content.append(line)
		if not found_export_ignore:
			content.extend(export_ignore)

	content = '\n'.join(content) + '\n'
	with open(attributes, 'wb') as f:
		f.write(content.encode('utf-8'))

def matches_patterns(value, patterns):
	for pattern in patterns:
		if fnmatch.fnmatch(value, pattern):
			return True
	return False

def list_directory(root, ignored=None):
	patterns_to_ignore = []
	for pattern in ignored or []:
		if pattern.startswith('/'):
			pattern = os.path.join('.', pattern.lstrip('/'))
		else:
			pattern = os.path.join('.', '**', pattern)
		patterns_to_ignore.append(pattern)
	for root, dirnames, filenames in os.walk(root):
		new_dirnames = []
		for dirname in dirnames:
			full_name = os.path.join(root, dirname)
			if matches_patterns(full_name, patterns_to_ignore):
				continue
			new_dirnames.append(dirname)
		dirnames[:] = new_dirnames

		for filename in filenames:
			full_name = os.path.join(root, filename)
			if matches_patterns(full_name, patterns_to_ignore):
				continue
			yield full_name

def fetch_repo(repo_root, url, force_removed=False):
	"""
	Remote Web repo should have following structure:

		http://<remote.host>/.../<reponame>/archive.tar.gz
		http://<remote.host>/.../<reponame>/sparse-checkout

	Repo URL will be:

		http://<remote.host>/.../<reponame>/

	Sparse-checkout file is optional.

	If force_removed is True, removes files from local copy that were removed from git archive in this very update.
	"""
	gitdir_info = os.path.join(repo_root, '.git', 'info')
	if not os.path.exists(gitdir_info):
		logging.error("Cannot find {0}. Is it .git repo at all?".format(gitdir_info))

	logging.info("Fetching archive...")
	if os.path.exists(os.path.join(gitdir_info, 'archive.tar')):
		os.rename(
				os.path.join(gitdir_info, 'archive.tar'),
				os.path.join(gitdir_info, 'archive.tar.bak'),
				)
	data = requests.get(url + '/archive.tar.gz', timeout=5).as_binary()
	with open(os.path.join(gitdir_info, 'archive.tar.gz'), 'wb') as f:
		f.write(data)

	logging.info("Fetching sparse checkout list...")
	try:
		data = requests.get(url + '/sparse-checkout', timeout=5).as_binary()
		with open(os.path.join(gitdir_info, 'sparse-checkout'), 'wb') as f:
			f.write(data)
	except Exception as e:
		logging.info("Failed to fetch sparse checkout file: {0}".format(e))
		pass

	logging.info("Unpacking archive...")
	subprocess.call(["gzip", "-d", os.path.join(gitdir_info, 'archive.tar.gz')])
	subprocess.call(["tar", "-xpf", os.path.join(gitdir_info, 'archive.tar')])

	logging.info("Removing empty directories...")
	for line in reversed(subprocess.check_output(["tar", "-tf", os.path.join(gitdir_info, 'archive.tar')]).decode('utf-8', 'replace').splitlines()):
		if not line.endswith('/'):
			continue
		if not os.listdir(line):
			os.rmdir(line)

	if os.path.exists(os.path.join(gitdir_info, 'archive.tar.bak')):
		logging.info("Checking removed archived files...")
		old_content = subprocess.check_output(['tar', '-tf', os.path.join(gitdir_info, 'archive.tar.bak')]).splitlines()
		new_content = subprocess.check_output(['tar', '-tf', os.path.join(gitdir_info, 'archive.tar')]).splitlines()
		for removed_file in set(old_content) - set(new_content):
			if os.path.isfile(removed_file):
				if force_removed:
					try:
						os.unlink(removed_file)
						logging.info('Removed file {0}'.format(removed_file))
					except:
						logging.warning('D  {0}'.format(removed_file))
						logging.error('Failed to remove file {0}'.format(removed_file))
				else:
					logging.warning('D  {0}'.format(removed_file))

		os.unlink(os.path.join(gitdir_info, 'archive.tar.bak'))

import argparse

def cli():
	parser = argparse.ArgumentParser(description=__doc__, epilog=fetch_repo.__doc__, formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-q', '--quiet', action='store_true', default=False, help='Show only critical messages.')
	commands = parser.add_subparsers(dest='command')
	clone_command = commands.add_parser('clone', description='Fetch git archive from remote url and setup local copy for future updates from the same URL.')
	clone_command.add_argument('url', help='Web location where git archive is accessible.')
	clone_command.add_argument('dest', nargs='?', help='Path to directory where git archive will be unpacked. By default uses last component of the URL.')
	pull_command = commands.add_parser('pull', description='Updates local copy using original remote URL.')
	pull_command.add_argument('--force-removed', action='store_true', default=False, help='Removes files from local copy that were removed from archive in this very update. By default just warns about them.')
	create_archive_command = commands.add_parser('create-archive', description='Creates archive for existing git repo and stores in .git/info/archive.tar.gz')
	create_archive_command.add_argument('--sparse-checkout', help='Custom sparse-checkout file. Only files from this list will be present in generated archive. By default tries to read .git/info/sparse-checkout.')
	status_command = commands.add_parser('status', description='Checks status of local copy. Currently only checks for "unversioned" files (i.e. missing from archive).')

	args = parser.parse_args()
	if args.quiet:
		logging.basicConfig(level=logging.WARNING)
	else:
		logging.basicConfig(level=logging.INFO)
	if args.command == 'clone':
		return clone(args.url, dest=args.dest)
	elif args.command == 'pull':
		return pull(force_removed=args.force_removed)
	elif args.command == 'create-archive':
		return create_archive(sparse_checkout=args.sparse_checkout)
	elif args.command == 'status':
		return status()
	logging.error('Unknown command: {0}'.format(args.command))
	return False

def create_archive(sparse_checkout=None):
	gitdir = '.git'
	if not os.path.isdir(gitdir):
		if os.path.isfile('HEAD'):
			logging.debug('.git/ is absent, but HEAD is found. Considering a bare Git repo.')
			gitdir = '.'
		else:
			logging.error("Cannot find .git/ in current directory. Is should be a root of a .git repo.")
			return False
	sparse_checkout = sparse_checkout or os.path.join(gitdir, 'info', 'sparse-checkout')
	if os.path.isfile(sparse_checkout):
		with open(sparse_checkout, 'r') as f:
			lines = f.read().splitlines()
		sparse_checkout = [line for line in lines if line and not line.startswith('#')]
		attributes = os.path.join(gitdir, 'info', 'attributes')
		export_ignore = []
		for line in subprocess.check_output(['git', 'ls-files']).decode('utf-8', 'replace').splitlines():
			if line not in sparse_checkout:
				export_ignore.append(line)
		update_sparse_checkout_attributes(attributes, export_ignore)
	subprocess.call(['git', 'archive', '-o', os.path.join(gitdir, 'info', 'archive.tar.gz'), 'HEAD'])

def clone(url, dest=None):
	url = url.rstrip('/')
	if dest is None:
		dest = posixpath.split(url)[-1]
	if not os.path.isdir(dest):
		os.makedirs(dest)
	os.chdir(dest)

	gitdir = '.git'
	if os.path.exists(gitdir):
		logging.error('Directory .git already exists: {0}'.format(gitdir))
		return False
	gitdir_info = os.path.join(gitdir, 'info')
	if not os.path.isdir(gitdir_info):
		os.makedirs(gitdir_info)

	logging.info("Cloning into {0}...".format(dest))
	with open(os.path.join(gitdir_info, 'pseudogit.url'), 'w') as f:
		f.write(url)
	fetch_repo('.', url)
	logging.info("Done.")

def pull(force_removed=False):
	gitdir = '.git'
	if not os.path.exists(gitdir):
		logging.error("Cannot find {0}. Is should be a root of a .git repo.".format(gitdir))
		return False
	gitdir_info = os.path.join(gitdir, 'info')
	with open(os.path.join(gitdir_info, 'pseudogit.url'), 'r') as f:
		url = f.read().strip()

	logging.info("Pulling remote {0}...".format(url))
	fetch_repo('.', url, force_removed=force_removed)
	logging.info("Done.")

def status():
	gitdir = '.git'
	if not os.path.exists(gitdir):
		logging.error("Cannot find {0}. Is should be a root of a .git repo.".format(gitdir))
		return False
	gitdir_info = os.path.join(gitdir, 'info')
	archive = os.path.join(gitdir_info, 'archive.tar')
	output = subprocess.check_output(["tar", "tf", archive])
	archived_files = set(os.path.join('.', line) for line in output.decode('utf-8', 'replace').splitlines())
	ignored = ['/.git']
	if os.path.isfile('.gitignore'):
		with open('.gitignore') as f:
			ignored += [line for line in f.read().splitlines() if line.strip() and not line.lstrip().startswith('#')]
	local_files = set(list_directory('.', ignored=ignored))
	for filename in local_files - archived_files:
		print('?? {0}'.format(filename))

if __name__ == '__main__':
	rc = cli()
	if rc is not None and rc is False:
		sys.exit(1)
