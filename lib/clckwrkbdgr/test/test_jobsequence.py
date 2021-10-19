import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'

import os, sys, subprocess, logging
import clckwrkbdgr.jobsequence
import clckwrkbdgr.jobsequence.sequence
import clckwrkbdgr.jobsequence.context
from clckwrkbdgr.jobsequence.context import WorkerStats
import clckwrkbdgr.jobsequence.script
from clckwrkbdgr.jobsequence import JobSequence
from pyfakefs import fake_filesystem_unittest
try: # pragma: no cover
	import pathlib2 as pathlib
	from pathlib2 import Path
except ImportError: # pragma: no cover
	import pathlib
	from pathlib import Path

def mock_iterdir(data):
	data = {Path(key):list(map(Path, values)) for key,values in data.items()}
	def _actual(self):
		result = data.get(self)
		assert result is not None, "Unexpected path in iterdir: {0}".format(self)
		return result
	return _actual

class TestJobSequence(unittest.TestCase):
	def _job_call(self, path):
		path = Path(path)
		return mock.call(path,
				'=== {0} : {1}\n'.format(
					Path(sys.modules['__main__'].__file__).name,
					path,
					),
				)
	def should_generate_verbose_option(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.verbose_option()
		click.option.assert_called_once_with('-v', '--verbose', count=True, help='Verbosity level.Passed to jobs via $MY_VERBOSE_VAR.Has cumulative value, each flag adds one level to verbosity and one character to environment variable: MY_VERBOSE_VAR=vvv.')
	def should_generate_job_dir_option(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.job_dir_option()
		click.option.assert_called_once_with('-d', '--dir', 'job_dirs', multiple=True, default=['my_default_dir'], show_default=True, help="Custom directory with job files. Can be specified several times, job files from all directories are sorted and executed in total order.")
	def should_generate_dry_run_option(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.dry_run_option()
		click.option.assert_called_once_with('--dry', 'dry_run', is_flag=True, help="Dry run. Only report about actions, do not actually execute them. Implies at least one level in verbosity.")
	def should_generate_patterns_argument(self):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		result = seq.patterns_argument()
		click.argument.assert_called_once_with('patterns', nargs=-1)
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable')
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({'my_default_dir':[]}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_run_job_sequence(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, None, verbose=0)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], '')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_not_called()
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False), (0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_default_dir') : [
			Path('my_default_dir')/'foo.2',
			Path('my_default_dir')/'bar',
			],
		Path('my_other_dir') : [
			Path('my_other_dir')/'foo.1',
			Path('my_other_dir')/'baz',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True, True])
	def should_run_several_job_dirs(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', ['my_default_dir', 'my_other_dir'], click=click)
		seq.run(None, None, verbose=0)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], '')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_default_dir', 'bar')),
				self._job_call(Path('my_other_dir', 'baz')),
				self._job_call(Path('my_other_dir', 'foo.1')),
				self._job_call(Path('my_default_dir', 'foo.2')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_default_dir') : [
			Path('my_default_dir')/'foo.2',
			Path('my_default_dir')/'bar',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True, False])
	def should_skip_missing_job_dirs(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', ['my_default_dir', 'my_other_dir'], click=click)
		seq.run(None, None, verbose=0)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], '')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_default_dir', 'bar')),
				self._job_call(Path('my_default_dir', 'foo.2')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_default_dir') : [
			Path('my_default_dir')/'foo',
			Path('my_default_dir')/'bar',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_run_verbose(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, None, verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_default_dir', 'bar')),
				self._job_call(Path('my_default_dir', 'foo')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_default_dir') : [
			Path('my_default_dir')/'foo',
			Path('my_default_dir')/'bar',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_perform_dry_run(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, None, verbose=2, dry_run=True)
		self.assertIsNone(os.environ.get('MY_VERBOSE_VAR'))
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_other_dir') : [
			Path('my_other_dir')/'foo',
			Path('my_other_dir')/'bar',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_run_on_specified_log_dir(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(None, 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_other_dir', 'bar')),
				self._job_call(Path('my_other_dir', 'foo')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(1, False), (2, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_other_dir') : [
			Path('my_other_dir')/'foo',
			Path('my_other_dir')/'bar',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_collect_return_codes(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		rc = seq.run(None, 'my_other_dir', verbose=2)
		self.assertEqual(rc, 3)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_other_dir', 'bar')),
				self._job_call(Path('my_other_dir', 'foo')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_other_dir') : [
			Path('my_other_dir')/'__pycache__',
			Path('my_other_dir')/'bar.py',
			Path('my_other_dir')/'baz.pyc',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_ignore_unwanted_files(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run([], 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_other_dir', 'bar.py')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_other_dir') : [
			Path('my_other_dir')/'foo',
			Path('my_other_dir')/'bar',
			Path('my_other_dir')/'baz',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_match_patterns(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(['ba'], 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_other_dir', 'bar')),
				self._job_call(Path('my_other_dir', 'baz')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_other_dir') : [
			Path('my_other_dir')/'foo',
			Path('my_other_dir')/'bar',
			Path('my_other_dir')/'baz',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_unmatch_patterns(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(['!ba'], 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_other_dir', 'foo')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_other_dir') : [
			Path('my_other_dir')/'foo',
			Path('my_other_dir')/'bar',
			Path('my_other_dir')/'baz',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_combine_patterns(self, path_is_dir, path_iterdir, subprocess_call, logging_info):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)
		seq.run(['ba', '!baz'], 'my_other_dir', verbose=2)
		self.assertEqual(os.environ['MY_VERBOSE_VAR'], 'vv')
		path_iterdir.assert_has_calls([])
		subprocess_call.assert_has_calls([
				self._job_call(Path('my_other_dir', 'bar')),
				])
	@mock.patch.dict(os.environ, os.environ.copy())
	@mock.patch('sys.exit')
	@mock.patch('logging.Logger.info')
	@mock.patch('clckwrkbdgr.jobsequence.sequence.run_job_executable', side_effect=[(0, False), (0, False)])
	@mock.patch.object(pathlib.Path, 'iterdir', autospec=True, side_effect=mock_iterdir({
		Path('my_default_dir') : [
			Path('my_default_dir')/'foo',
			Path('my_default_dir')/'bar',
			Path('my_default_dir')/'baz',
			],
		}))
	@mock.patch.object(pathlib.Path, 'is_dir', side_effect=[True])
	def should_run_cli(self, path_is_dir, path_iterdir, subprocess_call, logging_info, sys_exit):
		click = mock.MagicMock()
		seq = JobSequence('MY_VERBOSE_VAR', 'my_default_dir', click=click)

		seq.run = mock.MagicMock(return_value=1)
		click.command = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.verbose_option = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.dry_run_option = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.job_dir_option = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))
		seq.patterns_argument = mock.MagicMock(side_effect=lambda *args, **kwargs: (lambda x:x))

		seq.cli(['patterns'], None)

		seq.verbose_option.assert_called_with()
		seq.dry_run_option.assert_called_with()
		seq.job_dir_option.assert_called_with()
		seq.patterns_argument.assert_called_with()
		seq.run.assert_called_once_with(['patterns'], None, verbose=0, dry_run=False)
		sys_exit.assert_called_once_with(1)

class TestWorkerStats(fake_filesystem_unittest.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[clckwrkbdgr.jobsequence.context])
	def should_load_worker_stats_from_file(self):
		stats = WorkerStats.load('/test.worker')
		self.assertIsNone(stats.hostname)
		self.assertIsNone(stats.caps)

		self.fs.create_file('/test.worker', contents='')
		stats = WorkerStats.load('/test.worker')
		self.assertIsNone(stats.hostname)
		self.assertIsNone(stats.caps)

		self.fs.remove_object('/test.worker')
		self.fs.create_file('/test.worker', contents='hostname\n')
		stats = WorkerStats.load('/test.worker')
		self.assertEqual(stats.hostname, 'hostname')
		self.assertIsNone(stats.caps)

		self.fs.remove_object('/test.worker')
		self.fs.create_file('/test.worker', contents='hostname\ncaps\n')
		stats = WorkerStats.load('/test.worker')
		self.assertEqual(stats.hostname, 'hostname')
		self.assertEqual(stats.caps, 'caps')

		self.fs.remove_object('/test.worker')
		self.fs.create_file('/test.worker', contents='hostname\n666\n')
		stats = WorkerStats.load('/test.worker', caps_type=int)
		self.assertEqual(stats.hostname, 'hostname')
		self.assertEqual(stats.caps, 666)
	def should_save_worker_stats_to_file(self):
		stats = WorkerStats('hostname', None)
		stats.save('/test.worker')
		self.assertEqual(Path('/test.worker').read_text(), 'hostname\n')

		stats = WorkerStats('hostname', 'caps')
		stats.save('/test.worker')
		self.assertEqual(Path('/test.worker').read_text(), 'hostname\ncaps\n')
	def should_check_acceptance_of_worker_host_stats(self):
		__ = self.assertFalse
		OK = self.assertTrue

		# CURRENT:     host    caps                  STORED:     host  caps   REQ.caps
		OK(WorkerStats('this', None)   .is_preferred(WorkerStats(None, None), None))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats(None, None), 'False'))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats(None, None), 'True '))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', None), None))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', None), 'False'))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', None), 'True '))

		OK(WorkerStats('this', None)   .is_preferred(WorkerStats(None, None), None))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats(None, None), 'False'))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats(None, None), 'True '))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', 'False'), None))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', 'False'), 'False'))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', 'False'), 'True '))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', 'True'), None))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', 'True'), 'False'))
		__(WorkerStats('this', None)   .is_preferred(WorkerStats('other', 'True'), 'True '))

		OK(WorkerStats('this', 'False').is_preferred(WorkerStats(None, None), None))
		OK(WorkerStats('this', 'False').is_preferred(WorkerStats(None, None), 'False'))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats(None, None), 'True '))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats(None, None), None))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats(None, None), 'False'))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats(None, None), 'True '))

		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', None), None))
		OK(WorkerStats('this', 'False').is_preferred(WorkerStats('other', None), 'False'))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', None), 'True '))
		__(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', None), None))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', None), 'False'))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', None), 'True '))

		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', 'False'), None))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', 'False'), 'False'))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', 'False'), 'True '))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', 'True '), None))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', 'True '), 'False'))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('other', 'True '), 'True '))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', 'False'), None))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', 'False'), 'False'))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', 'False'), 'True '))
		__(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', 'True '), None))
		__(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', 'True '), 'False'))
		__(WorkerStats('this', 'True ').is_preferred(WorkerStats('other', 'True '), 'True '))

		OK(WorkerStats('this', 'False').is_preferred(WorkerStats('this', 'False'), None))
		OK(WorkerStats('this', 'False').is_preferred(WorkerStats('this', 'False'), 'False'))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('this', 'False'), 'True '))
		OK(WorkerStats('this', 'False').is_preferred(WorkerStats('this', 'True '), None))
		OK(WorkerStats('this', 'False').is_preferred(WorkerStats('this', 'True '), 'False'))
		__(WorkerStats('this', 'False').is_preferred(WorkerStats('this', 'True '), 'True '))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('this', 'False'), None))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('this', 'False'), 'False'))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('this', 'False'), 'True '))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('this', 'True '), None))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('this', 'True '), 'False'))
		OK(WorkerStats('this', 'True ').is_preferred(WorkerStats('this', 'True '), 'True '))
