import os, sys, subprocess
import configparser
from pathlib import Path
import functools, types
import contextlib
import logging
try:
	import termcolor
except ImportError:
	termcolor = types.SimpleNamespace()
	termcolor.colored = lambda s, *args, **kwargs: s
import clckwrkbdgr.fs

trace = logging.getLogger('setup')
class ColoredFormatter(logging.Formatter):
	COLORS = {
			'DEBUG': 'blue',
			'INFO': 'green',
			'WARNING': 'yellow',
			'CRITICAL': 'magenta',
			'ERROR': 'red',
			}
	def format(self, record):
		return termcolor.colored(
				super(ColoredFormatter, self).format(record),
				ColoredFormatter.COLORS.get(record.levelname, 'white'),
				)
_colored_stdout_handler = logging.StreamHandler()
_colored_stdout_handler.setFormatter(ColoredFormatter())
trace.addHandler(_colored_stdout_handler)

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
		- args  - condition's args (if there were any.
		- result  - actual result of the call of the condition function.
		"""
		def _decorator(func):
			func._needs_context = True
			return func
		return _decorator
	def with_name(self, name):
		""" Overrides name for condition.
		By default function's __name__ is used.
		"""
		def _decorator(func):
			func._condition_name = name
			return func
		return _decorator

	def when(self, condition, *condition_args):
		""" Decorator for function that tells Make to run the action function
		when condition is True.
		Condition should a callable that returns boolean value.
		If condition_args are supplied, they are passed to condition.
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
				condition_name = condition.__name__
				if hasattr(func, '_condition_name'):
					condition_name = func._condition_name
				condition_result = condition(*condition_args)
				if not condition_result:
					trace.info('Target {0} is up to date.'.format(condition_name))
					return True
				trace.warning('Target {0} is out of date.'.format(condition_name))
				if self._dry:
					trace.debug('Dry run, skipping action {0}'.format(func.__name__))
					return True
				trace.debug('Running action {0}'.format(func.__name__))
				try:
					if hasattr(func, '_needs_context') and func._needs_context:
						context = types.SimpleNamespace()
						context.condition = condition
						context.args = condition_args
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
	def unless(self, condition, *args):
		""" Decorator for function that tells Make to run the action function
		unless condition is met.
		See description of when() for other details.
		"""
		return self.when(functools.wraps(condition)(lambda *_args, condition=condition: not condition(*_args)), *args)

	@property
	def needs_network(self): # TODO not used anymore, should be removed?
		""" Tells Make that action needs network to be executed.
		Otherwise it should be skipped.
		"""
		def _decorator(func):
			@functools.wraps(func)
			def _wrapper(*args, **kwargs):
				if not self._network:
					trace.warning('Switched off {0} because network is off.'.format(func.__name__))
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
	with (Path('.git')/'config').open('a+') as f:
		f.write('[include]\n')
		f.write('	path=../.gitconfig\n')

def git_submodules_are_configured():
	gitconfig = configparser.ConfigParser()
	gitconfig.read([str(Path('.git')/'config')])
	gitmodules = configparser.ConfigParser()
	gitmodules.read(['.gitmodules'])
	return not (set(gitmodules.keys()) - set(gitconfig.keys()))

@make.unless(git_submodules_are_configured)
def init_git_submodules():
	return 0 == subprocess.call(['git', 'submodule', 'init'])

def bash_command(command):
	return 0 == subprocess.call(command, shell=True, executable='/bin/bash')

def is_symlink_to(dest, src):
	with clckwrkbdgr.fs.CurrentDir(Path(dest).parent):
		return Path(dest).is_symlink() and Path(src).resolve() == Path(dest).resolve()

def make_symlink(path, real_path):
	real_path = Path(real_path)
	real_path.parent.mkdir(parents=True, exists_ok=True)
	path = Path(path)
	path.parent.mkdir(parents=True, exists_ok=True)
	if path.exists():
		os.rename(str(path), str(path.with_suffix('.bak')))
	os.symlink(str(real_path), str(path))

class XDGSymlinks:
	""" Manages known XDG symlinks in XDG_CONFIG_HOME. """
	def __init__(self):
		self.known = []
	def ensure(self, symlink, real_file):
		""" Creates target 'ensure_xdg_symlink' to ensure that
		symlink exists and points to real_file. If not, symlink is created.
		Also tracks given symlink as known.
		"""
		self.known.append(symlink)
		def ensure_xdg_symlink(context):
			make_symlink(context.condition.dest, context.condition.src)
		ensure_xdg_symlink = make.with_context(ensure_xdg_symlink)
		ensure_xdg_symlink = make.with_name(symlink)(ensure_xdg_symlink)
		ensure_xdg_symlink = make.unless(is_symlink_to, symlink, real_file)(ensure_xdg_symlink)
	def ignore(self, symlink):
		""" Marks symlink as known without any actions.
		Useful for third-party symlinks.
		"""
		self.known.append(symlink)
	def is_known(self, filename):
		""" Checks if filename is amongst known symlinks. """
		try:
			return any(filename.samefile(known) for known in self.known)
		except:
			return any(filename.absolute() == known.absolute() for known in self.known)

known_symlinks = XDGSymlinks()

known_symlinks.ensure(Path.home()/'.macromedia', XDG_DATA_HOME/'macromedia')
known_symlinks.ensure(Path.home()/'.adobe', XDG_DATA_HOME/'macromedia')
known_symlinks.ensure(Path.home()/'.w3m', XDG_CONFIG_HOME/'w3m')
known_symlinks.ensure(Path.home()/'.profile', XDG_CONFIG_HOME/'profile')
known_symlinks.ensure(Path.home()/'.bashrc', XDG_CONFIG_HOME/'bash'/'bashrc')

known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'certificates', XDG_CACHE_HOME/'purple'/'certificates')
known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'telegram-purple', XDG_CACHE_HOME/'purple'/'telegram-purple')
known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'icons', XDG_CACHE_HOME/'purple'/'icons')
known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'xmpp-caps.xml', XDG_CACHE_HOME/'purple'/'xmpp-caps.xml')
known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'accels', XDG_CACHE_HOME/'purple'/'accels')
known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'logs', XDG_DATA_HOME/'purple'/'logs')

known_symlinks.ensure(Path.home()/'.freeciv', XDG_CONFIG_HOME/'freeciv')
known_symlinks.ensure(XDG_CONFIG_HOME/'freeciv'/'saves', XDG_DATA_HOME/'freeciv'/'saves')

known_symlinks.ensure(XDG_CONFIG_HOME/'xfce4'/'terminal', XDG_CONFIG_HOME/'Terminal')
known_symlinks.ensure(XDG_CONFIG_HOME/'vim'/'autoload'/'pathogen.vim', Path('..')/'bundle'/'pathogen'/'autoload'/'pathogen.vim')

# Third-party symlinks.
known_symlinks.ignore(XDG_CONFIG_HOME/'vim'/'bundle'/'vimoutliner'/'README.detailed')
known_symlinks.ignore(XDG_CONFIG_HOME/'firefox'/'lock')

def find_unknown_symlinks(root, known_symlinks):
	unknown = []
	for root, dirnames, filenames in os.walk(str(root)):
		root = Path(root)
		for filename in filenames + dirnames:
			filename = root/filename
			if not filename.is_symlink():
				continue
			trace.debug(filename)
			if known_symlinks.is_known(filename):
				continue
			unknown.append(filename)
	return unknown

@make.when(find_unknown_symlinks, XDG_CONFIG_HOME, known_symlinks)
@make.with_context
def notify_about_unknown_symlinks(context):
	trace.error('Found unknown symlinks:')
	trace.error(context.result)
	return not bool(context.result)

@functools.lru_cache()
def has_tmp_in_fstab():
	for line in Path('/etc/fstab').read_text().splitlines():
		if line.split()[:2] == ['tmpfs', '/tmp']:
			return True
	return False

@make.unless(has_tmp_in_fstab)
def tmp_should_be_mounted_as_tmpfs():
	trace.error('Add following line to /etc/fstab:')
	print('tmpfs /tmp tmpfs mode=1777,nosuid,nodev 0 0')
	return False # TODO way to fix automatically with sudo.

@functools.lru_cache()
def has_tmp_in_mount():
	for line in subprocess.check_output(['mount']).decode().splitlines():
		if line.split()[:3] == ['tmpfs', 'on', '/tmp']:
			return True
	return False

@make.unless(has_tmp_in_mount)
def tmp_should_be_mounted_as_tmpfs():
	trace.error('/tmp is not mounted as tmpfs!')
	trace.error('Restart might be needed.')
	return False # TODO way to fix automatically with sudo.

def XXkb_settings_missing_in_etc(etc_config_file):
	Xresources = XDG_CONFIG_HOME/'Xresources'
	local_XXkb = set([line for line in Xresources.read_text().splitlines() if line.startswith('XXkb.')])
	missing = local_XXkb - set(Path(etc_config_file).read_text().splitlines())
	return missing

@make.when(XXkb_settings_missing_in_etc, '/etc/X11/app-defaults/XXkb')
@make.with_context
def XXkb_should_be_set_in_etc(context):
	trace.error('These XXkb config lines are not present in {0}:'.format(context.args[-1]))
	for line in context.result:
		print(line)
	return False # TODO way to fix automatically with sudo.

@make.unless(is_symlink_to, '/etc/lastfmsubmitd.conf', XDG_DATA_HOME/'lastfm'/'lastfmsubmitd.conf')
@make.with_name('/etc/lastfmsubmitd.conf')
@make.with_context
def lastfmsubmitd_config_should_be_linked_to_etc(context):
	trace.error('{0} is not symlink to {1}'.format(context.args[0], context.args[1]))
	return False # TODO way to fix automatically with sudo.

LASTFMSUBMITD_MONIT = """\
check process lastfmsubmitd with pidfile /var/run/lastfm/lastfmsubmitd.pid
  start program = "/usr/sbin/service lastfmsubmitd restart"
  stop program = "/usr/sbin/service lastfmsubmitd stop"
  group lastfm
"""
MONIT_CONF_DIR = Path('/etc/monit/conf.d/')

def file_has_content(filename, content):
	filename = Path(filename)
	if not filename.is_file():
		return False
	if filename.read_text() != content:
		return False
	return True

@make.unless(file_has_content, MONIT_CONF_DIR/'lastfmsubmitd', LASTFMSUBMITD_MONIT)
@make.with_name(MONIT_CONF_DIR/'lastfmsubmitd')
@make.with_context
def monit_should_contain_lastfmsubmitd_entry(context):
	trace.error('{0} is missing or does not contain following content:'.format(context.args[0]))
	print(context.args[1])
	return False # TODO way to fix automatically with sudo.

@make.unless(os.path.isdir, '/run/lastfm')
@make.with_name('/run/lastfm')
@make.with_context
def lastfmsubmitd_runtime_dir_should_exist(context):
	trace.error('Directory {0} is missing.'.format(context.args[0]))
	trace.error('Create it and restart lastfmsubmitd service:')
	print('sudo /usr/sbin/service lastfmsubmitd restart')
	return False # TODO way to fix automatically with sudo.

def crontab_is_set():
	current_crontab = subprocess.check_output(['crontab', '-l'])
	basic_crontab = (XDG_CONFIG_HOME/'crontab').read_bytes()
	return basic_crontab in current_crontab

@make.unless(crontab_is_set)
def update_crontab():
	return 0 == subprocess.call(['update_crontab.py'])

def patch_is_applied(destfile, patch):
	with clckwrkbdgr.fs.CurrentDir(Path(destfile).parent):
		return 0 == subprocess.call(['patch', '-R', '-s', '-f', '--dry-run', str(destfile), '-i', str(patch)], stdout=subprocess.DEVNULL)

def apply_patch(destfile, patch):
	return 0 == subprocess.call(['patch', str(destfile), '-i', str(patch)])

@make.unless(patch_is_applied, Path('/usr/bin/when').expanduser(), XDG_CONFIG_HOME/'patch'/'when-1.1.36-xdg.patch')
@make.with_context
def patch_when(context):
	return apply_patch(*context.args) # TODO needs sudo


################################################################################

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Main setup script.')
	parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output. By default will print only errors and warnings.')
	parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true', default=False, help='Do not execute actions, just check conditions and report.')
	parser.add_argument('-N', '--no-network', dest='network', action='store_false', default=True, help='Skip targets that use network (e.g. on metered network connection or when there is no network at all).') # TODO isn't used anymore, should be removed?
	parser.add_argument('targets', nargs='*', help='Targets to make. By default makes all available targets one by one.')
	args = parser.parse_args()
	if args.verbose:
		trace.setLevel(logging.DEBUG)
	if not make.run(args.targets, dry=args.dry_run, network=args.network):
		sys.exit(1)
