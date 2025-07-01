import os, sys, subprocess
try:
	import clckwrkbdgr.vcs.git as git
except:
	sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
	try:
		import clckwrkbdgr.vcs.git as git
	except:
		for filename in ['lib/clckwrkbdgr/vcs/__init__.py', 'lib/clckwrkbdgr/vcs/git.py']:
			if not os.path.exists(os.path.dirname(filename)):
				os.makedirs(os.path.dirname(filename))
			if not os.path.exists(filename):
				with open(filename, 'wb') as f:
					f.write(subprocess.check_output(['git', 'show', 'master:{0}'.format(filename)]))
		import clckwrkbdgr.vcs.git as git

if __name__ == "__main__":
	quiet = '-q' in sys.argv[1:] or '--quiet' in sys.argv[1:]

	git.sync(quiet=quiet)

	if git.branch_is_behind_remote('master'):
		# Any unstaged files with no real diff (filtered by gitfilter)
		# will be restored to the stock version, so force stage them
		# to keep local changes intact.
		for filename in git.list_modified_files_with_no_real_changes():
			git.stage_file(filename)
		git.update('master', quiet=quiet)

	dotfiles_caps = os.path.join('.git', 'info', 'CAPS')
	if os.path.exists(dotfiles_caps):
		with open(dotfiles_caps) as f:
			caps = f.read().strip()
		if 0 != subprocess.call(['python', 'caps.py', 'sparse', caps]):
			git.SparseCheckout().sync(quiet=quiet)
