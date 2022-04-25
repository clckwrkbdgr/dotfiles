#!/usr/bin/env python
import os, sys, subprocess
from clckwrkbdgr import xdg, userstate
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME,
		verbose_var='DAILYUPDATE_VERBOSE',
		)

if userstate.get_flag('metered_network'):
	context.done()

import clckwrkbdgr.vcs.git as git
if not clckwrkbdgr.vcs.git.is_repo_root():
	context.done()

import clckwrkbdgr.pkg
required_caps = 'git'
current_caps = 'git' if clckwrkbdgr.pkg.is_app_installed("git") else 'arch'
if not context.validate_worker_host('dotfiles.submodules', caps_type=str, required_caps=required_caps, current_caps=current_caps):
	context.done()

context | git.update_submodules()
context.done()
