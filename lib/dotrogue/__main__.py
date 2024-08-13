import os, sys
from .messages import Log
from . import game
from .test.main import Tester

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	tester = Tester(rootdir=os.path.dirname(os.path.dirname(__file__)))
	if tester.need_tests(sys.argv, game.Savefile.last_save_time() if game.Savefile.exists() else -1):
		tests = tester.get_tests(sys.argv)
		rc = tester.run(tests, debug=debug)
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)
	Log.debug('started')
	game.run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
