import re
import logging
Log = logging.getLogger('projects.docs')
from collections import namedtuple
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path

Author = namedtuple('Author', 'name email')

def check(project_root_dir): # pragma: no cover -- TODO
	project_root_dir = Path(project_root_dir)
	errors = 0

	license = find_license(project_root_dir)
	if not license:
		print('{0}: LICENSE was not found'.format(project_root_dir))
		errors += 1

	authors = find_authors(license)
	if not authors:
		print('{0}: Authors are not found'.format(project_root_dir))
		errors += 1

	readme_file = find_readme(project_root_dir)
	if not readme_file:
		print('{0}: README was not found'.format(project_root_dir))
		errors += 1
	else:
		errors += check_readme(readme_file)
	return errors

def check_readme(readme_file): # pragma: no cover -- TODO
	errors = 0
	readme = readme_file.read_text()

	GITHUB_LINK = re.compile('https://github.com/[^/]+/[^/]+', flags=re.MULTILINE)
	if not GITHUB_LINK.search(readme):
		print('{0}: No links to github project.'.format(readme_file))
		errors += 1

	project_description = find_project_description(readme)
	if not project_description:
		print('{0}: No basic project description.'.format(readme_file))
		errors += 1

	installation_instructions = find_installation_instructions(readme)
	if not installation_instructions:
		print('{0}: No installation instructions.'.format(readme_file))
		errors += 1

	usage = find_usage_examples(readme)
	if not usage:
		print('{0}: No usage info or examples.'.format(readme_file))
		errors += 1

	docs_link = find_docs_link(readme)
	if not docs_link:
		print('{0}: No link to online documentation.'.format(readme_file))
		errors += 1

	return errors

def find_license(rootdir): # pragma: no cover -- TODO
	filename = rootdir/'LICENSE'
	if filename.exists():
		return filename
	Log.info("File LICENSE does not exist")
	return None

AUTHORS_IN_LICENSE_FILE = re.compile(r'^Copyright (c) \d+ ([A-Z][A-Za-z -]+) <(\S+@\S+)>$')

def find_authors(license_file): # pragma: no cover -- TODO
	if not license_file:
		Log.info("License file was not found, cannot get author info.")
		return None
	authors_line = license_file.read_text().split('\n', 1)[0]
	author = AUTHORS_IN_LICENSE_FILE.match(authors_line)
	if not author:
		Log.info("First line in license file was not recognized as author info.")
	else:
		author = Author(author.group(1), author.group(2))
		Log.info("Found author in license file: {0}".format(author))
		return [author]
	return None

def find_readme(rootdir): # pragma: no cover -- TODO
	standard_paths = [
			rootdir/'README',
			rootdir/'README.md',
			]
	for filename in standard_paths:
		if filename.exists():
			Log.info("Found readme in {0}".format(filename))
			return filename
		else:
			Log.info("File {0} does not exist".format(filename))

	return None

def find_project_description(text): # pragma: no cover -- TODO
	main_header_line = text.find('\n===')
	if main_header_line < 0:
		Log.info("No main header line is found in README.")
		return None
	main_header_line += 1

	second_header_line = text.find('\n---', main_header_line)
	if second_header_line < 0:
		Log.info("No secondary header line is found in README.")
		return None
	second_header_line = text.rfind('\n', main_header_line, second_header_line)

	description = text[main_header_line:second_header_line].lstrip('=').strip()
	Log.info("Found description: {0}".format(repr(description)))
	return description

def find_installation_instructions(text): # pragma: no cover -- TODO
	install_header = text.find('Installation\n---')
	if install_header < 0:
		Log.info("No 'Installation' header line is found in README.")
		return None
	return install_header

def find_usage_examples(text): # pragma: no cover -- TODO
	usage = text.find('Usage\n---')
	examples = text.find('Examples\n---')
	if usage < 0 and examples < 0:
		Log.info("No 'Usage' or 'Examples' header lines were found in README.")
		return None
	return usage or examples

def find_docs_link(text): # pragma: no cover -- TODO
	docs_link = re.search(r'https://readthedocs.io/\S+', text)
	if not docs_link:
		Log.info("No readthedocs links was found in README.")
		return None
	return docs.link.group(0)
