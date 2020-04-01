import os, sys, subprocess
import configparser
from pathlib import Path

_verbose = False
_actions = []

def unless(condition):
	def _decorator(func):
		def _wrapper(*args, **kwargs):
			if (condition() if callable(condition) else condition):
				if _verbose:
					print('Target {0} is up to date.'.format(condition))
				return True
			if _verbose:
				print('Running action {0}'.format(func))
			result = func(*args, **kwargs)
			if result is None:
				result = True
			if _verbose:
				if result:
					print('Action {0} is successful.'.format(func))
				else:
					print('Action {0} failed.'.format(func))
			return result
		_actions.append(_wrapper)
		return _wrapper
	return _decorator

always = unless(False)

################################################################################

def git_config_includes_gitconfig():
	gitconfig = configparser.ConfigParser()
	gitconfig.read([str(Path('.git')/'config')])
	return 'include' in gitconfig and 'path' in gitconfig['include'] and gitconfig['include']['path'] == '../.gitconfig'

@unless(git_config_includes_gitconfig)
def ensure_git_config_includes_gitconfig():
	(Path('.git')/'config').read_text().splitlines()
	with (Path('.git')/'config').open('a+') as f:
		f.write('[include]\n')
		f.write('	path=../.gitconfig\n')

@always
def update_git_submodules():
	subprocess.call(['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge'])

if __name__ == '__main__':
	args = sys.argv[1:]
	if args == ['verbose']:
		_verbose = True
	os.chdir(str(Path(__file__).parent))
	for action in _actions:
		if not action():
			if _verbose:
				print('Stop.')
			break
	else:
		print('Done.')
