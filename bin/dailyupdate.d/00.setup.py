#!/usr/bin/env python
import os, sys, subprocess
from clckwrkbdgr import xdg

os.chdir(str(xdg.XDG_CONFIG_HOME))
args = [sys.executable, 'setup.py']
if os.environ.get('DAILYUPDATE_VERBOSE'):
	args.append("--verbose")
sys.exit(subprocess.call(args))
