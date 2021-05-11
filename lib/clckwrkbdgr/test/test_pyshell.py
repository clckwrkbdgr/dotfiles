import os, sys, platform
import time
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import contextlib
try: # pragma: no cover
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
import clckwrkbdgr.fs
import clckwrkbdgr.pyshell as pyshell
from clckwrkbdgr.pyshell import sh
pyshell._unmonkeypatch_sys_exit()

class TestUtils(unittest.TestCase):
	def should_expand_lists_in_args(self):
		self.assertEqual(list(pyshell.expand_lists([])), [])
		self.assertEqual(list(pyshell.expand_lists(['a', 'b', 1, None])), ['a', 'b', 1, None])
		self.assertEqual(list(pyshell.expand_lists(['a', ['b', 'c'], 1, None])), ['a', 'b', 'c', 1, None])

class TestReturnCode(unittest.TestCase):
	def should_convert_returncode_to_string(self):
		self.assertEqual(str(pyshell.ReturnCode(0)), '0')
		self.assertEqual(repr(pyshell.ReturnCode(0)), 'ReturnCode(0)')
	def should_treat_returncode_as_bool(self):
		rc = pyshell.ReturnCode(0)
		self.assertTrue(bool(rc))
		self.assertTrue(rc)

		rc = pyshell.ReturnCode()
		self.assertTrue(bool(rc))
		self.assertTrue(rc)

		rc = pyshell.ReturnCode(1)
		self.assertFalse(bool(rc))
		self.assertFalse(rc)
	def should_treat_returncode_as_int(self):
		rc = pyshell.ReturnCode(0)
		self.assertEqual(int(rc), 0)
		self.assertEqual(rc, 0)

		rc = pyshell.ReturnCode()
		self.assertEqual(int(rc), 0)
		self.assertEqual(rc, 0)

		rc = pyshell.ReturnCode(-1)
		self.assertEqual(int(rc), -1)
		self.assertEqual(rc, -1)
	def should_compare_returncodes(self):
		self.assertEqual(pyshell.ReturnCode(-1), -1)
		self.assertEqual(pyshell.ReturnCode(-1), False)
		self.assertEqual(pyshell.ReturnCode(0), 0)
		self.assertEqual(pyshell.ReturnCode(0), True)
		self.assertNotEqual(pyshell.ReturnCode(-1), 0)
		self.assertNotEqual(pyshell.ReturnCode(-1), True)
		self.assertNotEqual(pyshell.ReturnCode(0), -1)
		self.assertNotEqual(pyshell.ReturnCode(0), False)

@contextlib.contextmanager
def TempArgv(*args): # TODO mocks
	try:
		old_argv = sys.argv[:]
		sys.argv[:] = list(args)
		yield
	finally:
		sys.argv = old_argv

@contextlib.contextmanager
def TempEnviron(var, value): # pragma: no cover: TODO mocks or move to separate module?
	old_value = None
	try:
		if var in os.environ:
			old_value = os.environ[var]
		if value is None:
			if var in os.environ:
				del os.environ[var]
		else:
			os.environ[var] = value
		yield
	finally:
		if old_value is None:
			if var in os.environ:
				del os.environ[var]
		else:
			os.environ[var] = old_value

class TestPyShell(unittest.TestCase): # TODO mocks
	def should_get_args(self):
		with TempArgv('progname', '-a', '--arg', 'value'):
			self.assertEqual(sh.ARGS(), ('-a', '--arg', 'value'))
			self.assertEqual(sh.ARG(0), 'progname')
			self.assertEqual(sh.ARG(1), '-a')
			self.assertEqual(sh.ARG(4), '')
	def should_chdir(self):
		with clckwrkbdgr.fs.CurrentDir('.'):
			expected = Path('.').resolve().parent
			sh.cd('..')
			actual = Path('.').resolve()
			self.assertEqual(actual, expected)
	def should_chdir_back(self):
		with clckwrkbdgr.fs.CurrentDir('.'):
			original = Path('.').resolve()
			parent = original.parent
			sh.cd('..')
			sh.cd('-')
			actual = Path('.').resolve()
			self.assertEqual(actual, original)
			sh.cd('-')
			actual = Path('.').resolve()
			self.assertEqual(actual, parent)
	def should_get_environment_variables(self):
		with TempEnviron('MY_VAR', 'my_value'):
			self.assertEqual(sh['MY_VAR'], 'my_value')
		with TempEnviron('MY_VAR', None):
			self.assertEqual(sh['MY_VAR'], '')
	def should_run_command(self):
		rc = sh.run('true')
		self.assertEqual(rc, 0)

		rc = sh.run('false')
		self.assertEqual(rc, 1)
	def should_nohup(self):
		start = time.time()
		rc = sh.run('sleep', '4', nohup=True)
		stop = time.time()
		self.assertTrue(stop - start < 3)
		self.assertIsNone(rc)
	def should_suppress_output(self):
		sh.run('echo', 'you should not see this!', stdout=None)
	def should_collect_output(self):
		output = sh.run('echo', 'test', stdout=str)
		self.assertEqual(output, 'test')
	def should_collect_stderr(self):
		with TempEnviron('LC_ALL', 'C'):
			output = sh.run('cat', 'definitely missing file', stdout=str, stderr='stdout')
		output = output.replace('/usr/bin/', '')
		output = output.replace('/bin/', '')
		output = output.replace("'", '')
		expected = "cat: cannot open definitely missing file" if platform.system() == 'AIX' else "cat: definitely missing file: No such file or directory"
		self.assertEqual(output, expected)
	def should_suppress_stderr(self):
		output = sh.run('cat', 'definitely missing file', stdout=str, stderr=None)
		self.assertEqual(output, '')
	def should_use_parentheses_to_run_command(self):
		output = sh('echo', 'test', stdout=str)
		self.assertEqual(output, 'test')
	def should_feed_stdin(self):
		output = sh.run('cat', stdin='foo\nbar', stdout=str)
		self.assertEqual(output, 'foo\nbar')

	def should_exit(self):
		with self.assertRaises(SystemExit) as e:
			sh.exit(1)
		self.assertEqual(e.exception.code, 1)

		with self.assertRaises(SystemExit) as e:
			sh.exit(0)
		self.assertEqual(e.exception.code, 0)
	def should_exit_with_code_from_last_command(self):
		sh('false')
		with self.assertRaises(SystemExit) as e:
			sh.exit()
		self.assertEqual(e.exception.code, 1)

		sh('true')
		with self.assertRaises(SystemExit) as e:
			sh.exit()
		self.assertEqual(e.exception.code, 0)
