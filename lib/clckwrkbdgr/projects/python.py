import os, sys
import re
import clckwrkbdgr.fs
from .. import lint
from . import docs

def qualify(project_root_dir): # pragma: no cover -- TODO
	for filename in clckwrkbdgr.fs.find(project_root_dir, exclude_dir_names=['.git', '.svn']):
		if filename.suffix == '.py':
			return True
	return False # TODO also check for python hashbangs

def check(project_root_dir): # pragma: no cover -- TODO
	rc = 0

	readme_file = docs.find_readme(project_root_dir)
	if readme_file:
		readme = readme_file.read_text()
		SUPPORTED_PYTHON_VERSIONS = re.compile('Supported Python versions:', flags=re.MULTILINE)
		if not SUPPORTED_PYTHON_VERSIONS.search(readme):
			print('{0}: No info about supported Python versions.'.format(readme_file))
			rc += 1

	for filename in clckwrkbdgr.fs.find(project_root_dir, exclude_dir_names=['.git', '.svn']):
		if filename.name == 'Makefile':
			content = filename.read_text()
			if 'python -m coverage' not in content: # TODO very dumb check. Also need check for actual unittest-discover call + mypy.
				print('{0}: coverage call is not found.'.format(filename))
				rc += 1
			break
	else:
		print('{0}: Makefile was not found'.format(project_root_dir))
		rc += 1

	return rc

def check_syntax(root): # pragma: no cover -- TODO
	import ast, traceback
	result = True
	for filename in clckwrkbdgr.fs.find(root, exclude_dir_names=['.git', '.svn']):
		if filename.suffix != '.py':
			continue
		if not lint.check_syntax(filename):
			result = False
	return result
