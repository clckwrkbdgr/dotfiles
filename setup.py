import os, sys, subprocess
import configparser
from pathlib import Path
import functools, types
import contextlib
import logging
trace = logging.getLogger('setup')
trace.addHandler(logging.StreamHandler())

class Make(object):
	""" Decorator factory and repository for setup actions."""
	def __init__(self, rootdir=None):
		""" If rootdir is not specified, uses parent dir of this script. """
		self._rootdir = rootdir or Path(__file__).parent
		self._dry = False
		self._network = True
		self._actions = []
	def run(self, targets=None, dry=False, network=True):
		""" Runs registered actions according to the order of definition and corresponding conditions.
		Changes directory to the rootdir (see __init__).
		If network is False, does not execute network-dependent actions (see @needs_network).
		"""
		self._dry = dry
		self._network = network
		os.chdir(str(self._rootdir))
		if targets:
			actions = []
			for target in targets:
				matching = [action for action in make._actions if action.__name__ == target]
				if not matching:
					trace.error('No such action defined: {0}'.format(target))
					return False
				actions.extend(matching)
		else:
			actions = make._actions
		for action in actions:
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

	@property
	def with_context(self):
		""" Marks functions which needs target context to be passed to.
		Context should be passed as the first argument of the action function.
		Context is a namespace with following fields:
		- condition  - condition function object passed to target.
		- result  - actual result of the call of the condition function.
		"""
		def _decorator(func):
			func._needs_context = True
			return func
		return _decorator

	def when(self, condition, name=None):
		""" Decorator for function that tells Make to run the action function
		when condition is True.
		Condition should a callable that returns boolean value.
		Returns True upon success, False otherwise.
		Function is expected to return object that can be casted to bool,
		with the exception of None (e.g. when there is no return statement at all):
		in this case None is treated as True (i.e. Ok).
		If name is specified, it is used as name of the target,
		otherwise name of the condition function is used.
		"""
		def _decorator(func):
			@functools.wraps(func)
			def _wrapper(*args, **kwargs):
				condition_name = name or condition.__name__
				condition_result = condition()
				if not condition_result:
					trace.info('Target {0} is up to date.'.format(condition_name))
					return True
				trace.info('Target {0} is out to date.'.format(condition_name))
				if self._dry:
					trace.info('Dry run, skipping action {0}'.format(func.__name__))
					return True
				trace.info('Running action {0}'.format(func.__name__))
				try:
					if hasattr(func, '_needs_context') and func._needs_context:
						context = types.SimpleNamespace()
						context.condition = condition
						context.result = condition_result
						args = (context,) + args
					result = func(*args, **kwargs)
					if result is None:
						result = True
				except Exception as e:
					trace.error(e, exc_info=True)
					result = False
				if result:
					trace.info('Action {0} is successful.'.format(func.__name__))
				else:
					trace.error('Action {0} failed.'.format(func.__name__))
				return result
			self._actions.append(_wrapper)
			return _wrapper
		return _decorator
	def unless(self, condition, name=None):
		""" Decorator for function that tells Make to run the action function
		unless condition is met.
		See description of when() for other details.
		"""
		return self.when(functools.wraps(condition)(lambda condition=condition: not condition()), name=name)

	@property
	def always(self):
		""" Tells Make to run function always, regardless of any condition. """
		def run_always(): return False
		run_always.__name__ = '<run always>'
		return self.unless(run_always)
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

XDG_CONFIG_HOME = Path('~/.config').expanduser()
XDG_DATA_HOME = Path('~/.local/share').expanduser()
XDG_CACHE_HOME = Path('~/.cache').expanduser()

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


def bash_command(command):
	def _actual_check(command=command):
		return 0 == subprocess.call(command, shell=True, executable='/bin/bash')
	_actual_check.__name__ = '`{0}`'.format(command)
	return _actual_check

@contextlib.contextmanager
def CurrentDir(path):
	try:
		old_cwd = os.getcwd()
		os.chdir(str(path))
		yield
	finally:
		os.chdir(old_cwd)

def is_symlink_to(dest, src):
	def _actual_check():
		with CurrentDir(Path(dest).parent):
			return Path(dest).is_symlink() and Path(src).resolve() == Path(dest).resolve()
	_actual_check.__name__ = str(dest)
	_actual_check.dest = Path(dest)
	_actual_check.src = Path(src)
	return _actual_check

def make_symlink(path, real_path):
	real_path = Path(real_path)
	dest.parent.mkdir(parents=True, exists_ok=True)
	path = Path(path)
	if path.exists():
		os.rename(str(path), str(path.with_suffix('.bak')))
	os.symlink(str(real_path), str(path))

@make.unless(bash_command('xdg && [ -h ~/.bashrc ]'))
def test_xdg():
	return False

@make.unless(bash_command('. xdg && [ -d "$XDG_CONFIG_HOME" ]'))
def test_xdg():
	return False

@make.unless(bash_command('. xdg && [ -d "$XDG_DATA_HOME" ]'))
def test_xdg():
	return False

@make.unless(bash_command('. xdg && [ -d "$XDG_CACHE_HOME" ]'))
def test_xdg():
	return False

@make.unless(bash_command('xdg && [ -h ~/.bashrc ]'))
def test_xdg():
	return False

@make.unless(bash_command('xdg && [ -h ~/.profile ]'))
def test_xdg():
	return False

@make.unless(bash_command('xdg && [ -h ~/.xinitrc ]'))
def test_xdg():
	return True # TODO actually isn't created by `xdg`, but should it be?

@make.unless(bash_command('xdg && [ -h ~/.w3m ]'))
def test_xdg():
	return False

@make.unless(bash_command('xdg && [ -h ~/.macromedia ]'))
def test_xdg():
	return False

@make.unless(bash_command('xdg && [ -h ~/.adobe ]'))
def test_xdg():
	return False

@make.unless(bash_command('. xdg && [ -d "$XDG_CACHE_HOME/vim" ]'))
def test_xdg():
	return False

known_symlinks = []

known_symlinks.append(XDG_CONFIG_HOME/'purple'/'certificates')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'purple'/'certificates', XDG_CACHE_HOME/'purple'/'certificates'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'purple'/'telegram-purple')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'purple'/'telegram-purple', XDG_CACHE_HOME/'purple'/'telegram-purple'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'purple'/'icons')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'purple'/'icons', XDG_CACHE_HOME/'purple'/'icons'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'purple'/'xmpp-caps.xml')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'purple'/'xmpp-caps.xml', XDG_CACHE_HOME/'purple'/'xmpp-caps.xml'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'purple'/'accels')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'purple'/'accels', XDG_CACHE_HOME/'purple'/'accels'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'purple'/'logs')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'purple'/'logs', XDG_DATA_HOME/'purple'/'logs'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'.freeciv'/'saves')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'.freeciv'/'saves', XDG_DATA_HOME/'freeciv'/'saves'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

known_symlinks.append(XDG_CONFIG_HOME/'vim'/'autoload'/'pathogen.vim')
@make.unless(is_symlink_to(XDG_CONFIG_HOME/'vim'/'autoload'/'pathogen.vim', Path('..')/'bundle'/'pathogen'/'autoload'/'pathogen.vim'))
@make.with_context
def create_xdg_symlink(context):
	make_symlink(context.condition.dest, context.condition.src)

# Third-party symlinks.
known_symlinks.append(XDG_CONFIG_HOME/'vim'/'bundle'/'vimoutliner'/'README.detailed')
known_symlinks.append(XDG_CONFIG_HOME/'firefox'/'lock')

def find_unknown_symlinks(root, known_symlinks):
	unknown = []
	for root, dirnames, filenames in os.walk(str(root)):
		root = Path(root)
		for filename in filenames:
			filename = root/filename
			if not filename.is_symlink():
				continue
			try:
				if any(filename.samefile(known) for known in known_symlinks):
					continue
			except:
				if any(filename.absolute() == known.absolute() for known in known_symlinks):
					continue
			unknown.append(filename)
	return unknown

@make.when(functools.wraps(find_unknown_symlinks)(functools.partial(find_unknown_symlinks, XDG_CONFIG_HOME, known_symlinks)))
@make.with_context
def notify_about_unknown_symlinks(context):
	print('Found unknown symlinks:')
	print(context.result)
	return not bool(context.result)

################################################################################

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Main setup script.')
	parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output. By default will print only errors and warnings.')
	parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true', default=False, help='Do not execute actions, just check conditions and report.')
	parser.add_argument('-N', '--no-network', dest='network', action='store_false', default=True, help='Skip targets that use network (e.g. on metered network connection or when there is no network at all).')
	parser.add_argument('targets', nargs='*', help='Targets to make. By default makes all available targets one by one.')
	args = parser.parse_args()
	if args.verbose:
		trace.setLevel(logging.INFO)
	if not make.run(args.targets, dry=args.dry_run, network=args.network):
		sys.exit(1)
