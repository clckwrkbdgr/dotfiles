from __future__ import print_function
import os, sys
from .system.logging import Log
from . import game
from . import ui
from .system import savefile
from .test.main import Tester

def run():
	sfile = savefile.Savefile()
	reader = sfile.load()
	if reader is not None:
		instance = game.Game(dummy=True)
		instance.load(reader)
	else:
		instance = game.Game()
	with ui.auto_ui()() as interface:
		instance.main_loop(interface)
	if instance.get_player() and instance.get_player().is_alive():
		with sfile.save(game.Version.CURRENT) as writer:
			instance.save(writer)
	else:
		sfile.unlink()

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	tester = Tester(rootdir=os.path.dirname(os.path.dirname(__file__)))
	if tester.need_tests(sys.argv, savefile.Savefile.last_save_time() if savefile.Savefile.exists() else -1, printer=print):
		tests = tester.get_tests(sys.argv)
		rc = tester.run(tests, debug=debug)
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)
	Log.debug('started')
	run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
