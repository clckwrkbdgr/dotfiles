import os, sys, subprocess
import difflib

class Stash(object):
	def __enter__(self):
		os.system("git stash")
		return self
	def __exit__(self, e, t, tb):
		if 0 != os.system("git stash pop"):
			# Resolving merge conflicts 'manually' to prevent leaving conflict markers in the code.
			os.system("git checkout --theirs .")
			os.system("git stash drop")

class GitFile(object):
	def __init__(self, branch, path):
		self.branch, self.path = branch, path
		self.content = subprocess.check_output('git show {0}:{1}'.format(self.branch, self.path))

class SparseCheckout(object):
	def __init__(self):
		self.basefile = os.path.join('.git', 'info', 'sparse-checkout')
		self.content = None
	def _load_content(self):
		if self.content:
			return
		with open(self.basefile, 'rb') as f:
			self.content = f.read()
	def is_same(self, content):
		self._load_content()
		return self.content == content
	def diff(self, content):
		self._load_content()
		return list(difflib.unified_diff(
			self.content.decode('utf-8', 'replace').splitlines(),
			content.decode('utf-8', 'replace').splitlines(),
			))
	def update_with(self, content):
		with open(self.basefile, 'wb') as f:
			f.write(content)

def branch_is_behind_remote(branch):
	try:
		output = subprocess.check_output(['git', 'for-each-ref', '--format="%(push:track)"', 'refs/heads/{0}'.format(branch)], stderr=subprocess.STDOUT)
		return b'behind' in output
	except subprocess.CalledProcessError as e:
		if b'unknown field name' in e.output:
			output = subprocess.check_output(['git', 'status', '-sb'.format(branch)])
			return b'behind' in output
		else:
			raise

if __name__ == "__main__":
	# Fetch remote updates status only.
	os.system("git remote update")

	if branch_is_behind_remote('master'):
		with Stash():
			os.system("git pull origin master")

	if branch_is_behind_remote('loader'):
		# Fetch loader branch in background without switching to it (and messing with current branch).
		os.system("git fetch origin loader:loader")
		# Detect changes in sparse checkout listing.
		listing = GitFile('loader', 'work.lst')
		sparse = SparseCheckout()
		if not sparse.is_same(listing.content):
			print('Updating sparse-checkout:')
			for line in sparse.diff(listing.content):
				print(line)
			sparse.update_with(listing.content)
			with Stash():
				os.system("git checkout master")
