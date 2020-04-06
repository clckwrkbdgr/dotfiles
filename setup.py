import os, sys, subprocess
import configparser
from pathlib import Path
import functools
import logging
trace = logging.getLogger('setup')
trace.addHandler(logging.StreamHandler())

class Make(object):
	""" Decorator factory and repository for setup actions."""
	def __init__(self, rootdir=None):
		""" If rootdir is not specified, uses parent dir of this script. """
		self._rootdir = rootdir or Path(__file__).parent
		self._network = True
		self._actions = []
	def run(self, network=True):
		""" Runs registered actions according to the order of definition and corresponding conditions.
		Changes directory to the rootdir (see __init__).
		If network is False, does not execute network-dependent actions (see @needs_network).
		"""
		self._network = network
		os.chdir(str(self._rootdir))
		for action in make._actions:
			try:
				result = action()
			except Exception as e:
				trace.error(e, exc_info=True)
				result = False
			if not result:
				trace.warning('Stop.')
				return False
		trace.info('Done.')
		return True

	def unless(self, condition):
		""" Decorator for function that tells Make to run the action function
		unless condition is met.
		Condition should a callable that returns boolean value.
		Returns True upon success, False otherwise.
		Function is expected to return object that can be casted to bool,
		with the exception of None (e.g. when there is no return statement at all):
		in this case None is treated as True (i.e. Ok).
		"""
		def _decorator(func):
			@functools.wraps(func)
			def _wrapper(*args, **kwargs):
				if condition():
					trace.info('Target {0} is up to date.'.format(condition.__name__))
					return True
				trace.info('Running action {0}'.format(func.__name__))
				result = func(*args, **kwargs)
				if result is None:
					result = True
				if result:
					trace.info('Action {0} is successful.'.format(func.__name__))
				else:
					trace.error('Action {0} failed.'.format(func.__name__))
				return result
			self._actions.append(_wrapper)
			return _wrapper
		return _decorator
	@property
	def always(self):
		""" Tells Make to run function always, regardless of any condition. """
		return self.unless(lambda:False)
	@property
	def needs_network(self):
		""" Tells Make that action needs network to be executed.
		Otherwise it should be skipped.
		"""
		def _decorator(func):
			@functools.wraps(func)
			def _wrapper(*args, **kwargs):
				if not self._network:
					trace.info('Switched off {0} because network is off.'.format(func.__name__))
					return None
				return func(*args, **kwargs)
			return _wrapper
		return _decorator

make = Make()

################################################################################

def git_config_includes_gitconfig():
	gitconfig = configparser.ConfigParser()
	gitconfig.read([str(Path('.git')/'config')])
	return 'include' in gitconfig and 'path' in gitconfig['include'] and gitconfig['include']['path'] == '../.gitconfig'

@make.unless(git_config_includes_gitconfig)
def ensure_git_config_includes_gitconfig():
	(Path('.git')/'config').read_text().splitlines()
	with (Path('.git')/'config').open('a+') as f:
		f.write('[include]\n')
		f.write('	path=../.gitconfig\n')

@make.always
@make.needs_network
def update_git_submodules():
	subprocess.call(['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge'])

@make.always
def test_xdg():
	assert 0 == subprocess.call('. xdg && [ -d "$XDG_CONFIG_HOME" ]', shell=True, executable='/bin/bash')
	assert 0 != subprocess.call('. xdg && [ -d "$XDG_DATA_HOME" ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('. xdg && [ -d "$XDG_CACHE_HOME" ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('xdg && [ -h ~/.bashrc ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('xdg && [ -h ~/.profile ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('xdg && [ -h ~/.xinitrc ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('xdg && [ -h ~/.w3m ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('xdg && [ -h ~/.macromedia ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('xdg && [ -h ~/.adobe ]', shell=True, executable='/bin/bash')
	assert 0 == subprocess.call('. xdg && [ -d "$XDG_CACHE_HOME/vim" ]', shell=True, executable='/bin/bash')

################################################################################

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Main setup script.')
	parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output. By default will print only errors and warnings.')
	parser.add_argument('-n', '--no-network', dest='network', action='store_false', default=True, help='Skip targets that use network (e.g. on metered network connection or when there is no network at all).')
	args = parser.parse_args()
	if args.verbose:
		trace.setLevel(logging.INFO)
	if not make.run(network=args.network):
		sys.exit(1)
