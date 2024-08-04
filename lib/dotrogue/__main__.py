import os, sys
from .messages import Log
from . import game

class Tester:
	def __init__(self):
		self.all_tests = []
	def iter_files(self):
		os.chdir(os.path.dirname(os.path.dirname(__file__)))
		for rootdir, dirnames, filenames in os.walk('dotrogue'):
			if '__pycache__' in rootdir:
				continue
			for filename in filenames:
				if filename.endswith('.pyc'):
					continue
				full_filename = os.path.join(rootdir, filename)
				if filename.startswith('test') and filename.endswith('.py'):
					self.all_tests.append(full_filename)
				yield full_filename
	def need_tests(self, argv):
		if 'test' in argv:
			return True
		last_save = game.Savefile.last_save_time()
		result = False
		for filename in self.iter_files():
			if os.stat(filename).st_mtime > last_save:
				print('Source file {0} has been changed.'.format(filename))
				result = True
		return result
	def get_tests(self, argv):
		tests = [arg for arg in argv if arg.startswith('dotrogue.')]
		if not tests:
			if not self.all_tests:
				list(self.iter_files())
			tests = self.all_tests
		return tests
	def run(self, tests, debug=False):
		command = ['python', '-m', 'coverage', 'run', '-m', 'unittest']
		if debug:
			command.append('--verbose')
		import subprocess
		rc = subprocess.call(command + tests)
		if rc != 0:
			sys.exit(rc)
		rc = subprocess.call(['python', '-m', 'coverage', 'report', '-m'])
		if rc != 0 or 'test' in sys.argv:
			sys.exit(rc)

def cli():
	debug = '--debug' in sys.argv
	if debug:
		Log.init('rogue.log')
	tester = Tester()
	if tester.need_tests(sys.argv):
		tests = tester.get_tests(sys.argv)
		tester.run(tests, debug=debug)
	Log.debug('started')
	game.run()
	Log.debug('exited')

if __name__ == '__main__':
	cli()
