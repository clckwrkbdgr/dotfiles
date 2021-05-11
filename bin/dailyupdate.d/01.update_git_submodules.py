#!/usr/bin/env python
import os, sys, subprocess
import logging
from clckwrkbdgr import xdg, userstate
logging.basicConfig(level=logging.DEBUG if os.environ.get('DAILYUPDATE_VERBOSE') else logging.WARNING)

if userstate.get_flag('metered_network'):
	sys.exit()

os.chdir(str(xdg.XDG_CONFIG_HOME))

def safe_int(value):
	try:
		return int(value)
	except ValueError:
		return value

try:
	git_version = tuple(map(safe_int, subprocess.check_output(['git', '--version']).decode().strip().split(None, 3)[2].split('.')))
except OSError as e:
	logging.info('Failed to detect Git version: {0}'.format(e))
	sys.exit()

args = ['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge']
if git_version >= (2, 26, 0):
	args += ['--single-branch']
subprocess.call(args)
submodule_info = subprocess.check_output(['git', 'submodule']).decode('utf-8', 'replace').splitlines()
