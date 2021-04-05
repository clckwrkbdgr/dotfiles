import os, sys, subprocess
import re, itertools, types
import logging, tempfile
from collections import defaultdict
try:
	from pathlib2 import Path
except ImportError: # pragma: py3 only
	from pathlib import Path
from clckwrkbdgr import utils
import clckwrkbdgr.winnt.registry as registry

def list_starts_with(main_list, prefix_list):
	if len(main_list) < len(prefix_list):
		return False
	for part, pattern in zip(main_list, prefix_list):
		if pattern == '*':
			continue
		if part != pattern:
			return False
	return True

def list_has_prefix(main_list, prefix_list):
	for part, pattern in zip(main_list, prefix_list):
		if pattern == '*':
			continue
		if part != pattern:
			return False
	return True

def parse_pattern_file(filename):
	for line in Path(filename).read_text().splitlines():
		values = re.split(r'[/\\]', line)
		if values:
			yield values

def save_snapshot(rootkey, dest_file, quiet=False):
	args = ["REG", "EXPORT", rootkey, str(dest_file), '/y']
	logging.debug(args)
	rc = subprocess.call(args, stdout=subprocess.DEVNULL if quiet else None)
	if rc != 0:
		logging.error("Failed to extract registry snapshot of {0}!".format(rootkey))
		return False
	return True

def remove_WOW6432Node_entry(keypath):
	return [entry for entry in keypath if entry != 'WOW6432Node']

def backup_registry_rootkeys(rootkeys, dest_file, exclude_patterns=None, quiet=False):
	exclude_patterns = list(exclude_patterns) or []
	tempfiles = []
	for rootkey in rootkeys:
		fhandle, filename = tempfile.mkstemp(suffix='.reg', prefix=rootkey)
		os.close(fhandle)
		filename = Path(filename)
		tempfiles.append(filename)
		if not save_snapshot(rootkey.upper(), filename, quiet=quiet):
			logging.error("Failed to backup registry!")
			return False
	with open(str(dest_file), 'w', encoding='utf-16') as f:
		parsed = itertools.chain.from_iterable(
				registry.iterate_with_context(registry.parse(filename))
				for filename in tempfiles
				)
		header_printed = False
		for context, entry in parsed:
			if context and any(list_starts_with(remove_WOW6432Node_entry(context), pattern) for pattern in exclude_patterns):
				continue
			if isinstance(entry, registry.Header):
				if header_printed:
					continue
				else:
					header_printed = True
			f.write(str(entry))
	for filename in tempfiles:
		os.unlink(str(filename))
	return True

def extract_part_of_snapshot(snapshot_file, exclude_patterns=None, include_patterns=None, output=None, quiet=False):
	output = output or sys.stdout
	exclude_patterns = list(exclude_patterns) or []
	include_patterns = list(include_patterns) or []
	parsed = registry.iterate_with_context(registry.parse(snapshot_file))
	header_printed = False
	for context, entry in parsed:
		if context and exclude_patterns and any(list_starts_with(remove_WOW6432Node_entry(context), pattern) for pattern in exclude_patterns):
			continue
		if context and include_patterns and not any(list_has_prefix(remove_WOW6432Node_entry(context), pattern) for pattern in include_patterns):
			continue
		if isinstance(entry, registry.Header):
			if header_printed:
				continue
			else:
				header_printed = True
		try:
			output.write(str(entry))
		except UnicodeError:
			try:
				output.write(str(entry).encode('utf-8', 'replace').decode('utf-8'))
			except UnicodeError:
				output.write(str(entry).encode('ascii', 'replace').decode('ascii'))

def mark_diff(lines, old_file_name):
	entries = iter(registry.iterate_with_context(registry.parse(old_file_name)))
	for line in lines:
		if line.startswith('>') or line == '---' or line.startswith('<'):
			yield line
			continue
		try:
			diff_context = re.match(r'^(\d+)(?:[,](\d+))?([acd])(\d+)(?:[,](\d+))?$', line)
			start, stop = diff_context.group(1), diff_context.group(2)
			action = diff_context.group(3)

			context, entry = next(entries)

			prev_context = context
			start = int(start)
			while entry.line_number <= start:
				prev_context = context
				context, entry = next(entries)
			affected = [prev_context]

			if stop:
				stop = int(stop)
				while entry.line_number <= stop:
					affected.append(context)
					context, entry = next(entries)

			if action == 'a':
				for context in affected:
					yield '# [NEW LINE(S) AFTER:] {0}'.format('\\'.join(context))
			else:
				for context in affected:
					yield '# {0}'.format('\\'.join(context))
		except Exception as e:
			yield '# ERROR: ' + str(e)
		yield line

import click

@click.group()
@click.option('--quiet', is_flag=True, help='Show less output')
@click.pass_context
def main(ctx, quiet=False):
	""" Utilities for Windows Registry. """
	ctx.obj = types.SimpleNamespace()
	ctx.obj.quiet = quiet

@main.command()
@click.argument('snapshot_file')
@click.option('-e', '--exclude', help='File with regkey prefixes to be excluded. Paths case-sensitive and are separated with slash (either direct or backward). Everything under prefix will be excluded. Values are considered part of the exclude path too (as the last component).')
@click.pass_obj
@utils.exits_with_return_value
def backup(args, snapshot_file, exclude=None):
	""" Creates backup file and filters it.

	Destination location of created and filtered SNAPSHOT FILE.
	"""
	quiet = args.quiet
	exclude_patterns = list(parse_pattern_file(exclude)) if exclude else []
	return backup_registry_rootkeys(['HKCU', 'HKLM'], snapshot_file, exclude_patterns=exclude_patterns, quiet=quiet)

@main.command()
@click.argument('snapshot_file')
@click.option('-i', '--include', help='File with regkey prefixes to be included. Paths are case-sensitive and are separated with slash (either direct or backward). Everything under prefix will be included (except patterns that are --excluded). Values are considered part of the include path too (as the last component).')
@click.option('-e', '--exclude', help='File with regkey prefixes to be excluded. Paths are case-sensitive and are separated with slash (either direct or backward). Everything under prefix will be excluded. Values are considered part of the exclude path too (as the last component).')
@click.pass_obj
@utils.exits_with_return_value
def extract(args, snapshot_file, exclude=None, include=None):
	""" Extracts part of registry snapshot file, prints to stdout.

	Expects prepared registry SNAPSHOT FILE.
	"""
	if not exclude and not include:
		logging.error("Expected at least one of the --exclude or --include arguments!")
		return False
	quiet = args.quiet
	exclude_patterns = list(parse_pattern_file(exclude)) if exclude else []
	include_patterns = list(parse_pattern_file(include)) if include else []
	return extract_part_of_snapshot(snapshot_file, exclude_patterns=exclude_patterns, include_patterns=include_patterns, quiet=quiet)

@main.command()
@click.argument('snapshot_file')
@utils.exits_with_return_value
def sort(snapshot_file):
	""" Sorts values within keys. Prints to stdout.

	Expects prepared registry SNAPSHOT FILE.
	"""
	output = sys.stdout
	for entry in umi.registry.sort(umi.registry.parse(snapshot_file)):
		try:
			output.write(str(entry))
		except UnicodeError:
			try:
				output.write(str(entry).encode('utf-8', 'replace').decode('utf-8'))
			except UnicodeError:
				output.write(str(entry).encode('ascii', 'replace').decode('ascii'))

@main.command()
@click.argument('diff_file')
@click.argument('old_file')
@utils.exits_with_return_value
def filterdiff(diff_file, old_file):
	""" Filters registry dump diff file and marks affected keys/values.
	Prints to stdout.

	Arguments:
	1. Registry dump diff file.
	2. Old registry dump file (read-only, for references).
	"""
	with open(diff_file) as f:
		for line in mark_diff(f.read().splitlines(), old_file):
			print(line)

@main.command()
@click.argument('snapshot_file')
@click.option('-n', '--topmost', type=int, default=40, help='Displays only this number of keys with largest sizes.')
@utils.exits_with_return_value
def stat(snapshot_file, topmost=40):
	""" Collects and prints stat on registry snapshot file.

	Currently supported are only the topmost keys with largest numbers of subkeys/values.
	"""
	all_sizes = defaultdict(int)
	for context, entry in umi.registry.iterate_with_context(umi.registry.parse(Path(snapshot_file).expanduser())):
		while context:
			all_sizes[context] +=1
			context = context[:-1]
	all_sizes = sorted(all_sizes.items(), key=lambda x: x[-1], reverse=True)
	for entry, size in all_sizes[:max(1, topmost)]:
		print(size, entry)

@main.command()
@click.option('--diff-command', help='External diff command (GNUdiff-compatible). By default will use simple `diff` on the PATH.')
@click.argument('old_file')
@click.argument('new_file')
@utils.exits_with_return_value
def diff(old_file, new_file, diff_command=None):
	""" Prints diff of two registry dump file.

	Arguments:
	1. Registry dump diff file.
	2. Old registry dump file (read-only, for references).
	"""
	p = subprocess.Popen([diff_command or 'diff', '-a', old_file, new_file], stdout=subprocess.PIPE)
	stdout, _ = p.communicate()
	rc = p.wait()
	if stdout:
		stdout = stdout.replace(b'\x00', b'')
		stdout = stdout.decode('utf-8', 'replace')
		for line in mark_diff(stdout.splitlines(), old_file):
			try:
				print(line)
			except UnicodeError:
				print(repr(line).encode('ascii', 'replace').decode('ascii', 'replace'))
	return rc

if __name__ == '__main__':
	main()
