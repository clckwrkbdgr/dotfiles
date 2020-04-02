import os, sys, subprocess
import configparser
from pathlib import Path
import logging
trace = logging.getLogger('setup')
trace.addHandler(logging.StreamHandler())

_actions = []

def unless(condition):
	def _decorator(func):
		def _wrapper(*args, **kwargs):
			if (condition() if callable(condition) else condition):
				trace.info('Target {0} is up to date.'.format(condition))
				return True
			trace.info('Running action {0}'.format(func))
			result = func(*args, **kwargs)
			if result is None:
				result = True
			if result:
				trace.info('Action {0} is successful.'.format(func))
			else:
				trace.error('Action {0} failed.'.format(func))
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
	if args == ['--verbose']:
		trace.setLevel(logging.INFO)
	os.chdir(str(Path(__file__).parent))
	for action in _actions:
		if not action():
			trace.warning('Stop.')
			break
	else:
		trace.info('Done.')
