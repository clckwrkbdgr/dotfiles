#!/usr/bin/env python
import os, sys, subprocess
import platform
from clckwrkbdgr import xdg, fs
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME/'lib',
		)

lock = fs.CrossHostFSMutex(xdg.save_state_path('dailyupdate')/'dotfiles_lib_unittest.lock')
lock.wait_lock(timeout=60)
with lock:
	context | subprocess.call(['unittest'] + context.quiet_arg("-q"), shell=(platform.system()=='Windows'))
	context.done()
