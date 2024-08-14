import os, sys, subprocess
from ..messages import Log

class Tester:
	def __init__(self, rootdir):
		self.rootdir = rootdir
		self.all_tests = []
	def iter_files(self):
		os.chdir(self.rootdir)
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
	def need_tests(self, argv, last_save, printer=None):
		if 'test' in argv:
			return True
		if last_save <= 0:
			return False
		result = False
		for filename in self.iter_files():
			if os.stat(filename).st_mtime > last_save:
				if printer:
					printer('Source file {0} has been changed.'.format(filename))
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
		command = ['python', '-m', 'coverage', 'run', '--source', 'dotrogue', '-m', 'unittest']
		if debug:
			command.append('--verbose')
		rc = subprocess.call(command + tests)
		if rc != 0:
			return rc
		rc = subprocess.call(['python', '-m', 'coverage', 'report', '-m'])
		return rc
