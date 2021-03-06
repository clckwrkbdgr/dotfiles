#!/usr/bin/env python
from __future__ import unicode_literals
import os, sys
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		working_dir=xdg.XDG_CONFIG_HOME,
		)

git_config_file = Path('.git')/'config'
if not git_config_file.is_file():
	context.done()

try:
	gitconfig = configparser.ConfigParser(strict=False)
except TypeError: # Py2 does not support not strict INIs.
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
	gitconfig = NotStrictConfigParser()
gitconfig.read([str(git_config_file)])
if gitconfig.has_section('include') and gitconfig.has_option('include', 'path') and gitconfig.get('include', 'path') == '../.gitconfig':
	context.done()

with (Path('.git')/'config').open('a+') as f:
	f.write('[include]\n')
	f.write('	path=../.gitconfig\n')
