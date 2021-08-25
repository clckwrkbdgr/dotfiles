""" Searches for any specification of license in given path(s) (recursively).
If path is not given, current path is used.
If option --git is given and CWD is a root of Git repo, search is performed in
Git-versioned content instead (bypassing working copy modifications/textconv).

Prints found resuls in in grep-like format '<filename>:<ln>:<found patterns>:<line>'
"""
import sys, os, re, subprocess

def list_files(path):
	path = path or '.'
	if os.path.isfile(path):
		yield path
		return
	for root, dirnames, filenames in os.walk(path):
		dirnames[:] = [dirname for dirname in dirnames if dirname != '.git']
		for filename in filenames:
			yield os.path.join(root, filename)

def fs_content(filename):
	with open(filename, 'rb') as f:
		for line in f:
			yield line

def git_ls_files(path):
	submodules = subprocess.check_output(['git', 'config', '--file', '.gitmodules', '--name-only', '--get-regexp', '[.]path$']).decode('utf-8', 'replace').splitlines()
	submodules = [line.split('.', 1)[1].rsplit('.', 1)[0] for line in submodules]
	for entry in subprocess.check_output(['git', 'ls-files']).decode('utf-8', 'replace').splitlines():
		if path and not entry.startswith(path):
			continue
		if entry in submodules:
			continue
		yield entry

def git_show(filename):
	for line in subprocess.check_output(['git', 'show', 'HEAD:{0}'.format(filename)]).splitlines():
		yield line

def grep(byte_lines, patterns):
	for line_number, line in enumerate(byte_lines):
		line = line.decode('utf-8', 'replace')
		for pattern in patterns:
			matches = pattern.findall(line)
			if matches:
				line = line.rstrip()[:120]
				yield line_number, ','.join(map(str, matches)) + ':' + line

PATTERNS = [re.compile(pattern, flags=re.I) for pattern in [
		r'\bMIT',
		r'\bMPL',
		r'\bGPL',
		r'licen[sc]e',
		]]

if __name__ == '__main__':
	args = sys.argv[1:] or [None]
	searcher, catter = list_files, fs_content
	if '--git' in args:
		if not os.path.exists('.git'):
			raise RuntimeError('Cannot use option --git in non-Git repo root.')
		searcher, catter = git_ls_files, git_show

	for path in args:
		for filename in searcher(path):
			if filename == __file__:
				continue
			for line_number, text in grep(catter(filename), PATTERNS):
				print('{0}:{1}:{2}'.format(filename, line_number, text))

