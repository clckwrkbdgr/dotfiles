import os, sys, subprocess

class Stash(object):
	def __enter__(self):
		os.system("git stash")
		return self
	def __exit__(self, e, t, tb):
		os.system("git stash pop")

class GitFile(object):
	def __init__(self, branch, path):
		self.branch, self.path = branch, path
		self.content = subprocess.check_output('git show {0}:{1}'.format(self.branch, self.path))

class SparseCheckout(object):
	def __init__(self, branch, path):
		self.basefile = os.path.join('.git', 'info', 'sparse-checkout')
	def is_same(self, content):
		with open(self.base, 'rb') as f:
			if f.read() != content:
				return False
		return True
	def update_with(self, content):
		with open(self.base, 'wb') as f:
			f.write(content)

def branch_is_behind_remote(branch):
	output = subprocess.check_output('git for-each-ref --format="%(push:track)" refs/heads/{0}'.format(branch))
	return b'behind' in output

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
			sys.stdout.write(listing.content.decode()) # TODO print diff instead.
			sparse.update_with(listing.content)
			with Stash():
				os.system("git checkout master")
