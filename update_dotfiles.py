import os, sys, subprocess

# Fetch remote updates status only.
os.system("git remote update")

# Check if master branch is behind remote/origin/master
output = subprocess.check_output('git for-each-ref --format="%(push:track)" refs/heads/master')
if b'behind' in output:
	# Stash current local changes, pull (fetch and merge) remote master and re-apply local changes back.
	os.system("git stash")
	os.system("git pull origin master")
	os.system("git stash pop")

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
		os.system("git stash")
		os.system("git checkout master")
		os.system("git stash pop")
