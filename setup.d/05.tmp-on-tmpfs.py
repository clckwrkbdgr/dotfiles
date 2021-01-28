import os, sys
import subprocess
import configparser
import logging
trace = logging.getLogger('setup')
from pathlib import Path
from clckwrkbdgr import xdg

def has_tmp_in_fstab():
	for line in Path('/etc/fstab').read_text().splitlines():
		if line.split()[:2] == ['tmpfs', '/tmp']:
			return True
	return False

def has_tmp_in_mount():
	for line in subprocess.check_output(['mount']).decode().splitlines():
		if line.split()[:3] == ['tmpfs', 'on', '/tmp']:
			return True
	return False

if not has_tmp_in_fstab():
	trace.error('Add following line to /etc/fstab:')
	print('tmpfs /tmp tmpfs mode=1777,nosuid,nodev 0 0')
	sys.exit(1) # TODO way to fix automatically with sudo.

if not has_tmp_in_mount():
	trace.error('/tmp is not mounted as tmpfs!')
	trace.error('Restart might be needed.')
	sys.exit(1) # TODO way to fix automatically with sudo.
