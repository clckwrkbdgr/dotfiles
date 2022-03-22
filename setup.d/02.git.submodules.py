#!/usr/bin/env python
import os, sys
import subprocess
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
	import re
	class NotStrictConfigParser(configparser.ConfigParser):
		OPTCRE = re.compile( # Overriden to allow whitespaces before options.
				r'\s*(?P<option>[^:=\s][^:=]*)'          # very permissive!
				r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
				# followed by separator
				# (either : or =), followed
				# by any # space/tab
				r'(?P<value>.*)$'                     # everything up to eol
				)
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME,
		)


try:
	gitconfig = configparser.ConfigParser(strict=False)
except TypeError: # Py2 does not support not strict INIs.
	gitconfig = NotStrictConfigParser()
gitconfig.read([str(Path('.git')/'config')])
try:
	gitmodules = configparser.ConfigParser(strict=False)
except TypeError: # Py2 does not support not strict INIs.
	gitmodules = NotStrictConfigParser()
gitmodules.read(['.gitmodules'])
if not (set(gitmodules.sections()) - set(gitconfig.sections())):
	context.done()

has_git = True
try:
	subprocess.check_call(['git', '--version'])
except subprocess.CalledProcessError:
	has_git = False
except OSError:
	has_git = False

if has_git:
	context | subprocess.call(['git', 'submodule', 'init'])
context.done()
