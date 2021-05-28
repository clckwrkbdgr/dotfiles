#!/usr/bin/env python
import os, sys, subprocess
from clckwrkbdgr import xdg
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME,
		verbose_var='DAILYUPDATE_VERBOSE',
		)

sys.exit(subprocess.call([sys.executable, 'setup.py'] + context.verbose_arg("--verbose")))
