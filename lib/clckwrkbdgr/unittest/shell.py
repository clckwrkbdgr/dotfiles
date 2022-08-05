import platform, subprocess
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
import clckwrkbdgr.xdg as xdg
from . import runner

@runner.test_suite('bash')
def bash_unittest(test, quiet=False): # pragma: no cover -- TODO
	unittest_bash = xdg.XDG_CONFIG_HOME/'lib'/'unittest.bash'
	bash = ['bash']
	if platform.system() == 'Windows':
		# WSL Bash does not read .profile or .bashrc when started from command line.
		bash = ['wsl', '--exec', 'bash', '-i'] # Need to start it interactively.
		# WSL Bash accepts only POSIX paths with drives as /mnt/<drive>/
		parts = list(unittest_bash.parts)
		parts[0] = '/mnt/{0}'.format(unittest_bash.drive.replace(':', '').lower())
		unittest_bash = Path(*parts).as_posix()
	else:
		unittest_bash = str(unittest_bash)
	args = bash + [str(unittest_bash)]
	if quiet:
		args += ['--quiet']
	args += [test or 'discover']
	rc = subprocess.call(args)
	return rc
