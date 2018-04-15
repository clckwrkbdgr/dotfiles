import os, sys, subprocess

class Stash(object):
	def __enter__(self):
		os.system("git stash")
		return self
	def __exit__(self, e, t, tb):
		os.system("git stash pop")

# Fetch remote updates status only.
os.system("git remote update")

# Check if master branch is behind remote/origin/master
output = subprocess.check_output('git for-each-ref --format="%(push:track)" refs/heads/master')
if b'behind' in output:
	with Stash():
		os.system("git pull origin master")

# Check if loader branch is behind remote/origin/loader
output = subprocess.check_output('git for-each-ref --format="%(push:track)" refs/heads/loader')
if b'behind' in output:
	# Fetch loader branch in background without switching to it (and messing with current branch).
	os.system("git fetch origin loader:loader")
	# Detect changes in sparse checkout listing.
	work_lst = subprocess.check_output('git show loader:work.lst')
	sparse_checkout = os.path.join('.git', 'info', 'sparse-checkout')
	diffs = False
	with open(sparse_checkout, 'rb') as f:
		if f.read() != work_lst:
			diffs = True
	if diffs:
		print('Updating sparse-checkout:')
		sys.stdout.write(work_lst.decode()) # TODO print diff instead.
		with open(sparse_checkout, 'wb') as f:
			f.write(work_lst)
		with Stash():
			os.system("git checkout master")
