import sys
from .messages import Log
from . import game

def files_have_changed():
	import os
	savefile = os.path.expanduser('~/.rogue.sav') # TODO take from game module
	last_save = os.stat(savefile).st_mtime
	for rootdir, dirnames, filenames in os.walk(os.path.dirname(__file__)):
		for filename in filenames:
			filename = os.path.join(rootdir, filename)
			if os.stat(filename).st_mtime > last_save:
				print('Source file {0} has been changed.'.format(filename))
				return True
	return False

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	if 'test' in sys.argv or files_have_changed():
		import os, subprocess
		os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
		tests = [arg for arg in sys.argv if arg.startswith('clckwrkbdgr.rogue.')]
		if not tests:
			for rootdir, dirnames, filenames in os.walk('clckwrkbdgr/rogue'):
				for filename in filenames:
					if filename.startswith('test') and filename.endswith('.py'):
						tests.append(os.path.join(rootdir, filename))
		command = ['python', '-m', 'coverage', 'run', '-m', 'unittest']
		if debug:
			command.append('--verbose')
		rc = subprocess.call(command + tests)
		if rc != 0:
			sys.exit(rc)
		rc = subprocess.call(['python', '-m', 'coverage', 'report', '-m'])
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)
	Log.debug('started')
	game.run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
