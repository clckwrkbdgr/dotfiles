import subprocess

def check_syntax(filename):
	return 0 == subprocess.call(['node', '--check', str(filename)])
