import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from . import main
import os

class TestTester(unittest.TestCase):
	@mock.patch('os.chdir')
	@mock.patch('os.walk')
	def should_iter_test_files(self, os_walk, os_chdir):
		os_walk.side_effect = [[
				('/rootdir/dotrogue', ['subdir', 'test', '__pycache__'], ['main.py', 'main.pyc']),
				('/rootdir/dotrogue/subdir', ['test', '__pycache__'], ['module.py', 'module.pyc']),
				('/rootdir/dotrogue/subdir/test', ['__pycache__'], ['test_module.py', 'test_module.pyc']),
				('/rootdir/dotrogue/test', ['__pycache__'], ['test_main.py', 'test_main.pyc']),
				('/rootdir/dotrogue/test/__pycache__', [], ['test_main.pyc']),
				]]
		tester = main.Tester('/rootdir')
		self.assertEqual(list(tester.iter_files()), [
			os.path.join('/rootdir/dotrogue', 'main.py'),
			os.path.join('/rootdir/dotrogue/subdir', 'module.py'),
			os.path.join('/rootdir/dotrogue/subdir/test', 'test_module.py'),
			os.path.join('/rootdir/dotrogue/test', 'test_main.py'),
			])
		self.assertEqual(tester.all_tests, [
			os.path.join('/rootdir/dotrogue/subdir/test', 'test_module.py'),
			os.path.join('/rootdir/dotrogue/test', 'test_main.py'),
			])
		os_chdir.assert_called_once_with('/rootdir')
	@mock.patch('os.chdir')
	@mock.patch('os.walk')
	def should_prepare_files_to_tests(self, os_walk, os_chdir):
		os_walk.side_effect = [[
				('/rootdir/dotrogue', ['subdir', 'test', '__pycache__'], ['main.py', 'main.pyc']),
				('/rootdir/dotrogue/subdir', ['test', '__pycache__'], ['module.py', 'module.pyc']),
				('/rootdir/dotrogue/subdir/test', ['__pycache__'], ['test_module.py', 'test_module.pyc']),
				('/rootdir/dotrogue/test', ['__pycache__'], ['test_main.py', 'test_main.pyc']),
				('/rootdir/dotrogue/test/__pycache__', [], ['test_main.pyc']),
				]]
		tester = main.Tester('/rootdir')
		self.assertEqual(tester.get_tests(['arg', 'dotrogue.test.test_foo', 'dotrogue.test.test_foo']), [
			'dotrogue.test.test_foo',
			'dotrogue.test.test_foo'
			])
		self.assertEqual(tester.get_tests(['arg']), [
			os.path.join('/rootdir/dotrogue/subdir/test', 'test_module.py'),
			os.path.join('/rootdir/dotrogue/test', 'test_main.py'),
			])
		self.assertEqual(tester.get_tests(['arg']), [
			os.path.join('/rootdir/dotrogue/subdir/test', 'test_module.py'),
			os.path.join('/rootdir/dotrogue/test', 'test_main.py'),
			])
		os_chdir.assert_called_once_with('/rootdir')
	@mock.patch('os.stat')
	@mock.patch('os.chdir')
	@mock.patch('os.walk')
	def should_detect_need_for_testing(self, os_walk, os_chdir, os_stat):
		os_walk.side_effect = [[
				('/rootdir/dotrogue', ['subdir', 'test', '__pycache__'], ['main.py', 'main.pyc']),
				('/rootdir/dotrogue/subdir', ['test', '__pycache__'], ['module.py', 'module.pyc']),
				('/rootdir/dotrogue/subdir/test', ['__pycache__'], ['test_module.py', 'test_module.pyc']),
				('/rootdir/dotrogue/test', ['__pycache__'], ['test_main.py', 'test_main.pyc']),
				('/rootdir/dotrogue/test/__pycache__', [], ['test_main.pyc']),
				]]*2
		class _OsStat:
			def __init__(self, value): self.st_mtime = value
		os_stat.side_effect = [
				_OsStat(10), # /rootdir/dotrogue/main.py
				_OsStat(10), # /rootdir/dotrogue/subdir/module.py
				_OsStat(10), # /rootdir/dotrogue/subdir/test/test_module.py
				_OsStat(10), # /rootdir/dotrogue/test/test_main.py

				_OsStat(10), # /rootdir/dotrogue/main.py
				_OsStat(666), # /rootdir/dotrogue/subdir/module.py
				_OsStat(10), # /rootdir/dotrogue/subdir/test/test_module.py
				_OsStat(666), # /rootdir/dotrogue/test/test_main.py
				]
		tester = main.Tester('/rootdir')
		printer_log = []
		def _print(value):
			printer_log.append(value)
		self.assertFalse(tester.need_tests(['arg'], -1, printer=_print))
		self.assertFalse(tester.need_tests(['arg'], 123, printer=_print))
		self.assertTrue(tester.need_tests(['arg'], 124, printer=_print))
		self.assertTrue(tester.need_tests(['test'], -1, printer=_print))
		self.assertTrue(tester.need_tests(['test'], 125, printer=_print))
		os_stat.assert_has_calls([
			mock.call(os.path.join('/rootdir/dotrogue', 'main.py')),
			mock.call(os.path.join('/rootdir/dotrogue/subdir', 'module.py')),
			mock.call(os.path.join('/rootdir/dotrogue/subdir/test', 'test_module.py')),
			mock.call(os.path.join('/rootdir/dotrogue/test', 'test_main.py')),

			mock.call(os.path.join('/rootdir/dotrogue', 'main.py')),
			mock.call(os.path.join('/rootdir/dotrogue/subdir', 'module.py')),
			mock.call(os.path.join('/rootdir/dotrogue/subdir/test', 'test_module.py')),
			mock.call(os.path.join('/rootdir/dotrogue/test', 'test_main.py')),
			])
		self.assertEqual(printer_log, [
			'Source file ' + os.path.join('/rootdir/dotrogue/subdir', 'module.py') + ' has been changed.',
			'Source file ' + os.path.join('/rootdir/dotrogue/test', 'test_main.py') + ' has been changed.',
			])
	@mock.patch('subprocess.call')
	def should_run_tests(self, subprocess_call):
		subprocess_call.side_effect = [
				0, 0,
				0, 0,
				1,
				0, 2,
				]
		tester = main.Tester('/rootdir')
		self.assertEqual(tester.run(['foo', 'bar']), 0)
		self.assertEqual(tester.run(['foo', 'bar'], debug=True), 0)
		self.assertEqual(tester.run(['foo', 'bar']), 1)
		self.assertEqual(tester.run(['foo', 'bar']), 2)
		subprocess_call.assert_has_calls([
			mock.call(['python', '-m', 'coverage', 'run', '--source', 'dotrogue', '-m', 'unittest', 'foo', 'bar']), # 0
			mock.call(['python', '-m', 'coverage', 'report', '-m']), # 0
			mock.call(['python', '-m', 'coverage', 'run', '--source', 'dotrogue', '-m', 'unittest', '--verbose', 'foo', 'bar']), # 0
			mock.call(['python', '-m', 'coverage', 'report', '-m']), # 0
			mock.call(['python', '-m', 'coverage', 'run', '--source', 'dotrogue', '-m', 'unittest', 'foo', 'bar']), # 1
			mock.call(['python', '-m', 'coverage', 'run', '--source', 'dotrogue', '-m', 'unittest', 'foo', 'bar']), # 0
			mock.call(['python', '-m', 'coverage', 'report', '-m']), # 2
			])
