import os, subprocess
import configparser
from pathlib import Path

def git_config_includes_gitconfig():
	gitconfig = configparser.ConfigParser()
	gitconfig.read([str(Path('.git')/'config')])
	return 'include' in gitconfig and 'path' in gitconfig['include'] and gitconfig['include']['path'] == '../.gitconfig'

def ensure_git_config_includes_gitconfig():
	if git_config_includes_gitconfig():
		return
	(Path('.git')/'config').read_text().splitlines()
	with (Path('.git')/'config').open('a+') as f:
		f.write('[include]\n')
		f.write('	path=../.gitconfig\n')

def update_git_submodules():
	subprocess.call(['git', 'submodule', 'update', '--init', '--remote', '--recursive', '--merge'])

if __name__ == '__main__':
	os.chdir(str(Path(__file__).parent))
	ensure_git_config_includes_gitconfig()
	update_git_submodules()
