from __future__ import print_function
import os, sys
from src.system.logging import Log
import src.game
import src.ui
import src.system.savefile
from src.test.main import Tester

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	tester = Tester(rootdir=os.path.dirname(__file__))
	if tester.need_tests(sys.argv, src.system.savefile.Savefile.last_save_time() if src.system.savefile.Savefile.exists() else -1, printer=print):
		tests = tester.get_tests(sys.argv)
		rc = tester.run(tests, debug=debug)
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)
	Log.debug('started')
	with src.system.savefile.AutoSavefile() as savefile:
		game = src.game.Game(load_from_reader=savefile.reader)
		with src.ui.auto_ui()() as ui:
			if game.main_loop(ui):
				savefile.save(game, src.game.Version.CURRENT)
	Log.debug('exited')

if __name__ == '__main__':
	cli()
