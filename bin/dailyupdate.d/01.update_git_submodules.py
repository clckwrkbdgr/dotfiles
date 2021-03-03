#!/usr/bin/env python
import os, sys, subprocess
from clckwrkbdgr import xdg, userstate

if userstate.get_flag('metered_network'):
	sys.exit()

os.chdir(str(xdg.XDG_CONFIG_HOME))

def safe_int(value):
	try:
		return int(value)
	except ValueError:
		return value

git_version = tuple(map(safe_int, subprocess.check_output(['git', '--version']).decode().strip().split(None, 3)[2].split('.')))

args = ['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge']
if git_version >= (2, 26, 0):
	args += ['--single-branch']
subprocess.call(args)
submodule_info = subprocess.check_output(['git', 'submodule']).decode('utf-8', 'replace').splitlines()
