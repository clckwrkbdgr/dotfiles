#!/usr/bin/env python3
import os, sys
import shutil
import tempfile

def setup_files_from_dir(src_dir, dir_name, dest_dir, actual_dir_name):
	backup_dotdir = src_dir + ".bak"

	os.makedirs(os.path.join(backup_dotdir, actual_dir_name), exist_ok=True)
	backup_dir_name = os.path.abspath(os.path.join(backup_dotdir, actual_dir_name))
	dotdir_name = os.path.abspath(os.path.join(src_dir, dir_name))
	dest_dir_name = os.path.abspath(os.path.join(dest_dir, actual_dir_name))

	print("Installing <{0}> to <{1}>.".format(dir_name, dest_dir_name))
	files = filter(lambda filename: not filename.startswith('_'), os.listdir(dotdir_name))
	for filename in files:
		if not os.path.isdir(dest_dir_name):
			os.makedirs(dest_dir_name, exist_ok=True)
		dest = os.path.join(dest_dir_name, filename)
		if dir_name == '.':
			dest = os.path.join(dest_dir_name, '.' + filename)
		dest = os.path.abspath(dest)
		dotfile_name = os.path.abspath(os.path.join(dotdir_name, filename))

		print("\t" + filename)
		if os.path.exists(dest) or os.path.islink(dest):
			# Attempt to simulate `mv --backup=t`
			if os.path.isfile(dest):
				shutil.copy(dest, dest + ".bak")
				shutil.move(dest + ".bak", backup_dir_name)
			shutil.move(dest, backup_dir_name)
			os.symlink(dotfile_name, dest)
		else:
			os.symlink(dotfile_name, dest)

def panic(message):
	print('Failed:', message)
	sys.exit(1)

def echo(value, filename):
	with open(filename, 'w') as f:
		f.write(value + '\n')

def cat(filename):
	with open(filename, 'r') as f:
		return f.read().rstrip()

def test_setup_files_from_dir():
	hostdir = tempfile.mkdtemp()
	os.mkdir(os.path.join(hostdir, 'dotfiles'))
	echo('value', os.path.join(hostdir, 'dotfiles', 'dotfile'))
	echo('old_value', os.path.join(hostdir, '.existing_dotfile'))
	echo('new_value', os.path.join(hostdir, 'dotfiles', 'existing_dotfile'))
	echo('existing_link', os.path.join(hostdir, 'dotfiles', 'existing_link'))
	os.symlink(os.path.join(hostdir, 'dotfiles', 'existing_link'),
			os.path.join(hostdir, '.existing_link'))
	os.mkdir(os.path.join(hostdir, 'dotfiles', '_config'))
	echo('config_value', os.path.join(hostdir, 'dotfiles', '_config', 'dotfile'))

	setup_files_from_dir(os.path.join(hostdir, 'dotfiles'), '.', hostdir, '.')
	setup_files_from_dir(os.path.join(hostdir, 'dotfiles'), '_config', hostdir, '.config')

	assert os.path.isdir(os.path.join(hostdir, 'dotfiles')), "dotfiles dir is missing!"
	assert os.path.isfile(os.path.join(hostdir, 'dotfiles', 'dotfile')), "original dotfiles are missing!"
	assert os.path.isfile(os.path.join(hostdir, 'dotfiles', 'existing_dotfile')),  "original dotfiles are missing!"
	assert os.path.isfile(os.path.join(hostdir, 'dotfiles', 'existing_link')),  "original dotfiles are missing!"
	assert os.path.isdir(os.path.join(hostdir, 'dotfiles', '_config')),  "config dotfiles dir is missing!"
	assert os.path.isfile(os.path.join(hostdir, 'dotfiles', '_config', 'dotfile')),  "original config dotfiles are missing!"

	assert os.path.isdir(os.path.join(hostdir, 'dotfiles.bak')),  "dotfiles backup dir is missing!"
	assert os.path.islink(os.path.join(hostdir, '.dotfile')),  ".dotfile is missing!"
	assert os.readlink(os.path.join(hostdir, '.dotfile')) == os.path.join(hostdir, 'dotfiles', 'dotfile'),  ".dotfile is incorrect!"

	assert os.path.islink(os.path.join(hostdir, '.existing_dotfile')),  ".existing_dotfile is missing!"
	assert os.readlink(os.path.join(hostdir, '.existing_dotfile')) == os.path.join(hostdir, 'dotfiles', 'existing_dotfile'),  ".existing_dotfile is incorrect!"
	assert os.path.isfile(os.path.join(hostdir, 'dotfiles.bak', '.existing_dotfile')),  ".existing_dotfile backup is missing!"
	assert cat(os.path.join(hostdir, '.existing_dotfile')) == "new_value",  ".existing_dotfile is incorrect!"
	assert cat(os.path.join(hostdir, 'dotfiles.bak', '.existing_dotfile')) == "old_value",  ".existing_dotfile backup is incorrect!"

	assert os.path.islink(os.path.join(hostdir, '.existing_link')),  ".existing_link is missing!"
	assert os.readlink(os.path.join(hostdir, '.existing_link')) == os.path.join(hostdir, 'dotfiles', 'existing_link'),  ".existing_link is incorrect!"
	assert os.path.islink(os.path.join(hostdir, 'dotfiles.bak', '.existing_link')),  ".existing_link backup is missing!"
	assert os.readlink(os.path.join(hostdir, 'dotfiles.bak', '.existing_link')) == os.path.join(hostdir, 'dotfiles', 'existing_link'),  ".existing_link backup is incorrect!"

	assert os.path.isdir(os.path.join(hostdir, '.config')),  ".config dir is missing!"
	assert os.path.islink(os.path.join(hostdir, '.config', 'dotfile')),  ".config', 'dotfile is missing!"
	assert os.readlink(os.path.join(hostdir, '.config', 'dotfile')) == os.path.join(hostdir, 'dotfiles', '_config', 'dotfile'),  ".config', 'dotfile is incorrect!"
	print('Done. Ok.')

def main():
	dotdir = os.path.join(os.path.expanduser('~'), 'dotfiles')
	homedir = os.path.expanduser('~')

	arg = sys.argv[1] if len(sys.argv) > 1 else ''
	if arg == "test":
		test_setup_files_from_dir()
	elif arg == "check":
		print("TODO")
		return 1
	elif arg == "setup":
		setup_files_from_dir(dotdir, '.', homedir, '.')
		setup_files_from_dir(dotdir, '_config', homedir, '.config')
		setup_files_from_dir(dotdir, '_bin', homedir, 'bin')
	else:
		print("Usage: ./_dotfiles.sh {setup|test|check}")
		print("    setup - install dotfiles on their places in HOMEDIR.")
		print("            Original files are stored in ~/dotfile.bak directory.")
		print("    test  - test dotfiles setup function.")
		print("    check - check for dotfiles (and dotdirs)  which aren't handled by script.")

if __name__ == "__main__":
	sys.exit(main())
