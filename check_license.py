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

PATTERNS = [re.compile(pattern) for pattern in [
		r'\bMIT(?:v|\b)',
		r'\bMPL[^A]',
		r'\bGPL',
		]]
PATTERNS += [re.compile(pattern, flags=re.I) for pattern in [
		r'licen[sc]e',
		]]

IGNORED_PATHS = list(map(os.path.abspath, [
	__file__,
	'.gitattributes', # Contains references to this file.
	'LICENSE', 'README.md', # Contains actual license info.
	'firefox/searchplugins/google.xml', # External plugin, TODO: move from dotfiles to personal storage.
	'gimp/pluginrc', # External plugin, TODO: should be loaded on-demand and not stored in config.
	'libreoffice/4/user/basic/Standard/Module1.xba', # External plugin, TODO: should be loaded on-demand and not stored in config.
	'libreoffice/4/user/extensions/bundled/registry/com.sun.star.comp.deployment.configuration.PackageRegistryBackend/lu5876ngu13x.tmp/OptionsDialog.xcu', # External plugin, TODO: should be loaded on-demand and not stored in config.
	'libreoffice/4/user/extensions/bundled/registry/com.sun.star.comp.deployment.configuration.PackageRegistryBackend/lu5876ngu13y.tmp/Filter.xcu', # External plugin, TODO: should be loaded on-demand and not stored in config.
	'libreoffice/4/user/extensions/bundled/registry/com.sun.star.comp.deployment.configuration.PackageRegistryBackend/lu5876ngu140.tmp/Paths.xcu', # External plugin, TODO: should be loaded on-demand and not stored in config.
	'gtk-3.0/gtk.css', # FIXME: violation of GPL, should create own theme.
	]))

if __name__ == '__main__':
	args = sys.argv[1:]
	searcher, catter = list_files, fs_content
	if '--git' in args:
		if not os.path.exists('.git'):
			raise RuntimeError('Cannot use option --git in non-Git repo root.')
		searcher, catter = git_ls_files, git_show
		args.remove('--git')

	for path in args or [None]:
		for filename in searcher(path):
			if os.path.abspath(filename) in IGNORED_PATHS:
				continue
			for line_number, text in grep(catter(filename), PATTERNS):
				print('{0}:{1}:{2}'.format(filename, line_number, text))

