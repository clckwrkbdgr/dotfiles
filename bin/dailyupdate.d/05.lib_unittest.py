#!/usr/bin/env python
import os, sys, subprocess
import platform
from clckwrkbdgr import xdg
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME/'lib',
		)

context | subprocess.call(['unittest'] + context.quiet_arg("-q"), shell=(platform.system()=='Windows'))
context.done()
