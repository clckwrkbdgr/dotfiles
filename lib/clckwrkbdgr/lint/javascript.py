import subprocess

def check_syntax(filename, quiet=False):
	return 0 == subprocess.call(['node', '--check', str(filename)],
			stdout=subprocess.DEVNULL if quiet else None,
			stderr=subprocess.DEVNULL if quiet else None,
			)
