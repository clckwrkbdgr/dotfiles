import os, sys, subprocess
try:
	subprocess.DEVNULL
except:
	subprocess.DEVNULL = open(os.devnull, 'w')
import difflib
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path

def is_repo_root(path='.'):
	return (Path(path)/'.git').is_dir()

class Stash(object):
	""" Context manager to make temporary stash and revert it back completely despite merge errors. """
	def __enter__(self):
		subprocess.call(["git", "stash"])
		return self
	def __exit__(self, e, t, tb):
		if 0 != subprocess.call(["git", "stash", "pop"]):
			# Resolving merge conflicts 'manually' to prevent leaving conflict markers in the code.
			subprocess.call(["git", "checkout", "--theirs", "."])
			subprocess.call(["git", "stash", "drop"])

class GitFile(object):
	""" Access to file stored in git objects. """
	def __init__(self, branch, path):
		self.branch, self.path = branch, path
		self.content = subprocess.check_output(['git', 'show', '{0}:{1}'.format(self.branch, self.path)])

class SparseCheckout(object):
	def __init__(self):
		self.basefile = os.path.join('.git', 'info', 'sparse-checkout')
		self.content = None
	def _load_content(self):
		if self.content:
			return
		with open(self.basefile, 'rb') as f:
			self.content = f.read()
	def lines(self):
		return self._load_content().splitlines()
	def sync(self, quiet=False):
		""" Synchronizes current state with sparse checkout list.
		May fix sparse checkout issues, but can lose local changes.
		"""
		quiet_arg = ['--quiet'] if quiet else []
		with Stash():
			return 0 == subprocess.call(["git", "checkout"] + quiet_arg + ["master"])
	def is_same(self, content):
		""" Returns True is current sparse info is the same as given content (raw text). """
		self._load_content()
		return self.content == content
	def diff(self, content):
		""" Returns diff between current sparse info and given content (raw text). """
		self._load_content()
		return list(difflib.unified_diff(
			self.content.decode('utf-8', 'replace').splitlines(),
			content.decode('utf-8', 'replace').splitlines(),
			))
	def update_with(self, content):
		""" Updates current sparse info with given content (raw text). """
		with open(self.basefile, 'wb') as f:
			f.write(content)

def branch_is_behind_remote(branch):
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

def sync(quiet=False):
	""" Synchronizes info about remote repository.
	No actual update/pull/push is performed.
	"""
	# Fetch remote updates status only.
	return 0 == subprocess.call(["git", "remote", "update"], stdout=(subprocess.DEVNULL if quiet else None))

def update(branch='master', quiet=False):
	""" Performs full update (fetch+merge) of given Git branch.
	Tries to resolve conflicts if possible.
	Updates submodules as well.
	"""
	quiet_arg = ['--quiet'] if quiet else []
	with Stash():
		subprocess.call(["git", "pull"] + quiet_arg + ["origin", "master"])
		subprocess.call(["git", "submodule"] + quiet_arg + ["init"])
		subprocess.call(["git", "submodule"] + quiet_arg + ["update", "--recursive"])

def list_attributes(attribute, filenames=None):
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

