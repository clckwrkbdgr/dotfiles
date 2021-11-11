#!/usr/bin/env python
import os, sys, subprocess
from clckwrkbdgr import xdg
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME,
		)

HOOK_PROXY = """#!/bin/bash
git/hooks/{0}
exit $?
"""

hookdir = os.path.join('.git', 'hooks')
for entry in os.listdir(os.path.join('git', 'hooks')):
	dest = os.path.join(hookdir, entry)
	if not os.path.exists(dest):
		with open(dest, 'wb') as f:
			f.write(HOOK_PROXY.format(entry).encode('utf-8', 'replace'))
			subprocess.call(['chmod', '+x', dest])
		context.info("Hook initialized: {0}".format(dest))
