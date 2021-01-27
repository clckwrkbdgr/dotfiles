import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'

import os, subprocess, logging
from clckwrkbdgr.jobsequence import JobSequence

class TestJobSequence(unittest.TestCase):
	def should_generate_verbose_option(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.verbose_option()
		click.option.assert_called_once_with('-v', '--verbose', count=True, help='Verbosity level.Passed to jobs via $MY_VERBOSE_VAR.Has cumulative value, each flag adds one level to verbosity and one character to environment variable: MY_VERBOSE_VAR=vvv.')
	def should_generate_job_dir_option(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.job_dir_option()
		click.option.assert_called_once_with('-d', '--dir', 'job_dir', default='my_default_dir', show_default=True, help="Custom directory with job files.")
	def should_generate_patterns_argument(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.patterns_argument()
		click.argument.assert_called_once_with('patterns', nargs=-1)
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.info')
	@mock.patch('subprocess.call')
	@mock.patch('os.listdir', return_value=[])
	def should_run_job_sequence(self, os_listdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, None, verbose=0)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], '')
		os_listdir.assert_called_once_with('my_default_dir')
		subprocess_call.assert_not_called()
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.info')
	@mock.patch('subprocess.call', side_effect=[0, 0])
	@mock.patch('os.listdir', return_value=['foo', 'bar'])
	def should_run_verbose(self, os_listdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, None, verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		os_listdir.assert_called_once_with('my_default_dir')
		subprocess_call.assert_has_calls([
				mock.call([os.path.join('my_default_dir', 'bar')], shell=True),
				mock.call([os.path.join('my_default_dir', 'foo')], shell=True),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.info')
	@mock.patch('subprocess.call', side_effect=[0, 0])
	@mock.patch('os.listdir', return_value=['foo', 'bar'])
	def should_run_on_specified_log_dir(self, os_listdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		os_listdir.assert_called_once_with('my_other_dir')
		subprocess_call.assert_has_calls([
				mock.call([os.path.join('my_other_dir', 'bar')], shell=True),
				mock.call([os.path.join('my_other_dir', 'foo')], shell=True),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.info')
	@mock.patch('subprocess.call', side_effect=[1, 2])
	@mock.patch('os.listdir', return_value=['foo', 'bar'])
	def should_collect_return_codes(self, os_listdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		rc = seq.run(None, 'my_other_dir', verbose=2)
		self.assertEqual(rc, 3)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		os_listdir.assert_called_once_with('my_other_dir')
		subprocess_call.assert_has_calls([
				mock.call([os.path.join('my_other_dir', 'bar')], shell=True),
				mock.call([os.path.join('my_other_dir', 'foo')], shell=True),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.info')
	@mock.patch('subprocess.call', side_effect=[0, 0])
	@mock.patch('os.listdir', return_value=['foo', 'bar', 'baz'])
	def should_match_patterns(self, os_listdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(['ba'], 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		os_listdir.assert_called_once_with('my_other_dir')
		subprocess_call.assert_has_calls([
				mock.call([os.path.join('my_other_dir', 'bar')], shell=True),
				mock.call([os.path.join('my_other_dir', 'baz')], shell=True),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('sys.exit')
	@mock.patch('logging.info')
	@mock.patch('subprocess.call', side_effect=[0, 0])
	@mock.patch('os.listdir', return_value=['foo', 'bar', 'baz'])
	def should_run_cli(self, os_listdir, subprocess_call, logging_info, sys_exit):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)

		seq.run = mock.MagicMock(return_value=1)
		click.command = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.verbose_option = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.job_dir_option = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.patterns_argument = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))

		seq.cli(['patterns'], None)

		seq.verbose_option.assert_called_with()
		seq.job_dir_option.assert_called_with()
		seq.patterns_argument.assert_called_with()
		seq.run.assert_called_once_with(['patterns'], None, verbose=0)
		sys_exit.assert_called_once_with(1)
