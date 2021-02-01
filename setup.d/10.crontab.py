#!/usr/bin/env python
import os, sys, subprocess
import platform
from clckwrkbdgr import xdg

os.chdir(str(xdg.XDG_CONFIG_HOME/'bin'))

current_crontab = subprocess.check_output(['crontab', '-l'], shell=(platform.system() == 'Windows'))
basic_crontab = (xdg.XDG_CONFIG_HOME/'crontab').read_bytes()
if basic_crontab in current_crontab:
	sys.exit()

sys.exit(subprocess.call(['update_crontab.py'], shell=(platform.system() == 'Windows')))
