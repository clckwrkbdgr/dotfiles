import os, sys, subprocess
try:
	subprocess.DEVNULL
except: # pragma: no cover -- py2
	subprocess.DEVNULL = open(os.devnull, 'w')
import difflib
try:
	from pathlib2 import Path, PurePosixPath
except ImportError: # pragma: no cover -- py2
	from pathlib import Path, PurePosixPath
import logging
import clckwrkbdgr.fs

def safe_int(value):
	try:
		return int(value)
	except ValueError:
		return value

def version(): # pragma: no cover -- TODO commands
	try:
		return tuple(map(safe_int, subprocess.check_output(['git', '--version']).decode().strip().split(None, 3)[2].split('.')))
	except OSError as e:
		return None

def is_repo_root(path='.'):
	return (Path(path)/'.git'/'HEAD').is_file()

def get_repo_root(): # pragma: no cover -- TODO commands
	git = subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE)
	if git.returncode != 0:
		return None
	return Path(git.stdout.decode().splitlines()[0]).resolve()

def get_repo_name(): # pragma: no cover -- TODO commands
	return get_repo_root().name

def find_repos(root='.'): # pragma: no cover -- TODO commands
	for root, dirnames, filenames in os.walk(str(root), followlinks=True):
		if '.git' not in dirnames:
			continue
		dirnames = dirnames[:]
		yield Path(root).resolve()

class Stash(object): # pragma: no cover -- TODO commands
	""" Context manager to make temporary stash and revert it back completely despite merge errors. """
	def __init__(self, quiet=False, keep_index=False):
		self._quiet = quiet
		self._keep_index = keep_index
	def __enter__(self):
		args = ["git", "stash"]
		if self._quiet:
			args.append('--quiet')
		if self._keep_index:
			args.append('--keep-index')
		subprocess.call(args)
		return self
	def __exit__(self, e, t, tb):
		quiet_arg = ['--quiet'] if self._quiet else []
		if 0 != subprocess.call(["git", "stash", "pop"] + quiet_arg):
			# Resolving merge conflicts 'manually' to prevent leaving conflict markers in the code.
			subprocess.call(["git", "checkout", "--theirs", "."])
			subprocess.call(["git", "stash", "drop"])

class GitFile(object): # pragma: no cover -- TODO commands
	""" Access to file stored in git objects. """
	def __init__(self, branch, path):
		self.branch, self.path = branch, path
		self.content = subprocess.check_output(['git', 'show', '{0}:{1}'.format(self.branch, self.path)])

class SparseCheckout(object): # pragma: no cover -- TODO commands
	def __init__(self):
		self.basefile = os.path.join('.git', 'info', 'sparse-checkout')
		self.content = None
	def _load_content(self):
		if self.content:
			return self.content
		with open(self.basefile, 'rb') as f:
			self.content = f.read()
		return self.content
	def lines(self, as_str=False):
		content = self._load_content()
		if as_str:
			content = content.decode('utf-8', 'replace')
		return content.splitlines()
	def sync(self, quiet=False):
		""" Synchronizes current state with sparse checkout list.
		May fix sparse checkout issues, but can lose local changes.
		"""
		quiet_arg = ['--quiet'] if quiet else []
		with Stash(quiet=quiet):
			return 0 == subprocess.call(["git", "checkout"] + quiet_arg + ["master"])
	def is_same(self, raw_content):
		""" Returns True is current sparse info is the same as given content (raw text). """
		self._load_content()
		return self.content == raw_content
	def diff(self, raw_content):
		""" Returns diff between current sparse info and given content (raw text). """
		self._load_content()
		return list(difflib.unified_diff(
			self.content.decode('utf-8', 'replace').splitlines(),
			raw_content.decode('utf-8', 'replace').splitlines(),
			))
	def update_with(self, raw_content):
		""" Updates current sparse info with given content (raw text). """
		with open(self.basefile, 'wb') as f:
			f.write(raw_content)

def branch_is_behind_remote(branch): # pragma: no cover -- TODO commands
	""" Returns True if given branch is behind remote origin. """
	try:
		output = subprocess.check_output(['git', 'for-each-ref', '--format="%(push:track)"', 'refs/heads/{0}'.format(branch)], stderr=subprocess.STDOUT)
		return b'behind' in output
	except subprocess.CalledProcessError as e:
		if b'unknown field name' in e.output:
			# Too old Git. Trying to check branches upstream status manually.
			with open('.git/refs/heads/{0}'.format(branch), 'rb') as f:
				local = f.read()
			if not os.path.exists('.git/refs/remotes/origin/{0}'.format(branch)):
				print("Upstream for branch '{0}' is not found!".format(branch))
				return False
			with open('.git/refs/remotes/origin/{0}'.format(branch), 'rb') as f:
				remote = f.read()
			return remote != local
		else:
			raise

def branch_is_ahead_remote(): # pragma: no cover -- TODO commands
	args = ["git", "status", '--porcelain', '--branch']
	git = subprocess.run(args, stdout=subprocess.PIPE)
	if git.returncode != 0:
		return False
	return b'ahead' in git.stdout

def sync(quiet=False): # pragma: no cover -- TODO commands
	""" Synchronizes info about remote repository.
	No actual update/pull/push is performed.
	"""
	# Fetch remote updates status only.
	return 0 == subprocess.call(["git", "remote", "update"], stdout=(subprocess.DEVNULL if quiet else None))

def push(remote='origin', branch='master'): # pragma: no cover -- TODO commands
	subprocess.run(["git", "push", remote, branch, "--tags"])

def update(branch='master', remote='origin', display_status=False, quiet=False): # pragma: no cover -- TODO commands
	""" Performs full update (fetch+merge) of given Git branch.
	Tries to resolve conflicts if possible.
	Updates submodules as well.
	"""
	if not subprocess.check_output(['git', 'remote']).strip():
		return
	quiet_arg = ['--quiet'] if quiet else []
	with Stash(quiet=quiet):
		subprocess.call(["git", "pull"] + quiet_arg + [remote, branch])
		subprocess.call(["git", "submodule"] + quiet_arg + ["init"])
		subprocess.call(["git", "submodule"] + quiet_arg + ["update", "--recursive"])
		if display_status:
			subprocess.call(["git", "status", '--short'])
			subprocess.call(["git", '--no-pager', "diff"])

def update_or_clone(url, name=None, branch='master', remote='origin', display_status=False, quiet=False): # pragma: no cover -- TODO commands
	if not name:
		name = PurePosixPath(url).name
		if name.endswith('.git'):
			name = name[:-4]
	if not Path(name).is_dir():
		subprocess.call(['git', 'clone', url, name])
	else:
		with clckwrkbdgr.fs.CurrentDir(name):
			sync(quiet=quiet)
			update(quiet=quiet)

def update_submodules(): # pragma: no cover -- TODO commands
	args = ['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge']
	if version() >= (2, 26, 0):
		args += ['--single-branch']
	return 0 == subprocess.call(args)

def list_submodules(): # pragma: no cover -- TODO commands
	""" Returns paths relative to current repo root. """
	return subprocess.check_output(['git', 'submodule', '-q', 'foreach', 'echo $sm_path']).decode('utf-8', 'replace').splitlines()

def list_remotes(): # pragma: no cover -- TODO commands
	return subprocess.run(["git", "remote"], stdout=subprocess.PIPE).stdout.decode().splitlines()

def list_branches(): # pragma: no cover -- TODO commands
	return subprocess.run(['git', 'for-each-ref', 'refs/heads/', '--format=%(refname:short)'], stdout=subprocess.PIPE).stdout.decode().splitlines()

def add_local_remote(name, path, bare=True): # pragma: no cover -- TODO commands
	existed = os.path.exists(str(path))
	if existed:
		logging.warning('Remote path already exists, considering bare repo already inited.')
		return True
	if not existed:
		command = ["git", "init"]
		if bare:
			command += ["--bare"]
		command += [path]
		subprocess.run(command)
	subprocess.run(["git", "remote", "add", name, path])
	if not existed:
		subprocess.run(["git", "push", "-u", name, "master", "--tags"])
	return True

def list_attributes(attribute, filenames=None): # pragma: no cover -- TODO commands
	""" Lists attributes for given files (or all versioned files by default).
	Yields pairs (<filename>, <attribute or None>).
	"""
	if filenames:
		filenames = b'\n'.join(filename.encode('utf-8', 'replace') for filename in filenames)
	else:
		filenames = subprocess.check_output(['git', 'ls-files'])
	git = subprocess.Popen(['git', 'check-attr', '--stdin', attribute], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
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

def has_staged_files(): # pragma: no cover -- TODO commands
	return 0 != subprocess.call(['git', 'diff', '--cached', '--quiet', '--exit-code'])

def file_needs_commit(path): # pragma: no cover -- TODO commands
	if 0 != subprocess.call(['git', 'diff', '--quiet', '--exit-code', str(path)]):
		return True # Unstaged, but modified.
	if 0 != subprocess.call(['git', 'ls-files', '--error-unmatch', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
		return True # Yet untracked.
	return False

def commit(paths, message=None): # pragma: no cover -- TODO commands
	for path in paths:
		subprocess.call(['git', 'add', path])
	command = ['git', 'commit']
	if not paths:
		command += ['-a']
	if message:
		command += ['-m', str(message)]
	return 0 == subprocess.call(command)

def commit_one_file(path, commit_message, show_diff=False): # pragma: no cover -- TODO commands
	if not Path(path).exists():
		raise RuntimeError('Cannot find file to commit in current WD: {0} ({1})'.format(path, os.getcwd()))
	if has_staged_files():
		raise RuntimeError('Some files are staged, cannot commit new file: {0}'.format(path))
	if not file_needs_commit(path):
		logging.debug('{0}: No changes, skipping'.format(path))
		return False # No changes.
	if show_diff:
		subprocess.call(['git', '--no-pager', 'diff', str(path)])
	subprocess.call(['git', 'add', str(path)])
	rc = subprocess.call(['git', 'commit', '--quiet', '-m', str(commit_message)])
	return rc == 0