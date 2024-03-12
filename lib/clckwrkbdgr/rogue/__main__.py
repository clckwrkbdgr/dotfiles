import sys
from .messages import Log
from . import game

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	Log.debug('started')
	game.run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
