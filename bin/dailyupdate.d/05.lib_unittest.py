#!/usr/bin/env python
import os, sys, subprocess
import platform
from clckwrkbdgr import xdg

os.chdir(str(xdg.XDG_CONFIG_HOME/'lib'))
args = ['unittest']
if not os.environ.get('DAILYUPDATE_VERBOSE'):
	args.append("-q")
sys.exit(subprocess.call(args, shell=(platform.system()=='Windows')))
