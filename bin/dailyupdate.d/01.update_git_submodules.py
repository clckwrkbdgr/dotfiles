#!/usr/bin/env python
import os, sys, subprocess
from clckwrkbdgr import xdg, userstate

if userstate.get_flag('metered_network'):
	sys.exit()

os.chdir(str(xdg.XDG_CONFIG_HOME))

git_version = tuple(map(int, subprocess.check_output(['git', '--version']).decode().strip().split(None, 3)[2].split('.')))
print(git_version)

args = ['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge']
if git_version >= (2, 26, 0):
	args += ['--single-branch']
subprocess.call(args)
submodule_info = subprocess.check_output(['git', 'submodule']).decode('utf-8', 'replace').splitlines()
if not any(line.startswith('+') for line in submodule_info):
	sys.exit()

# Having "(new commits)" in `git submodule`.
subprocess.call(['git', 'stash', '--keep-index'])
paths = subprocess.check_output(['git', 'submodule', '-q', 'foreach', 'echo $sm_path']).decode('utf-8', 'replace').splitlines()
for sm_path in paths:
	subprocess.call(['git', 'add', sm_path])
subprocess.call(['git', 'commit', '-m', 'Updated submodules.'])
subprocess.call(['git', 'stash', 'pop'])
