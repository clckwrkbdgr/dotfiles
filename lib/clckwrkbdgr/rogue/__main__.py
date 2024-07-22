import sys
from .messages import Log
from . import game

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	if 'test' in sys.argv:
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
		subprocess.check_call(command + tests)
		sys.exit()
	Log.debug('started')
	game.run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
