from clckwrkbdgr import unittest
from clckwrkbdgr.unittest import mock

import os
import datetime
import six
from clckwrkbdgr import xdg
import clckwrkbdgr.taskwarrior
import clckwrkbdgr.taskwarrior._base
from clckwrkbdgr.taskwarrior import Config, Entry, Stat, TaskWarrior

class TestTaskEntry(unittest.TestCase):
	def should_compare_entries(self):
		self.assertTrue(Entry(1, 'bar') < Entry(1, 'baz'))
		self.assertTrue(Entry(1, 'baz') > Entry(1, 'bar'))
		self.assertTrue(Entry(1, 'bar') < Entry(2, 'bar'))
		self.assertEqual(Entry(1, 'foo'), Entry(1, 'foo'))
		self.assertNotEqual(Entry(1, 'bar'), Entry(2, 'bar'))
		self.assertFalse(Entry(1, 'bar') == Entry(2, 'bar'))
		self.assertTrue(Entry(1, 'bar') != Entry(2, 'bar'))
	def should_iter_over_fields(self):
		self.assertEqual(list(Entry(1, 'bar')), [1, 'bar'])
	def should_repr_entries(self):
		self.assertEqual(str(Entry(1, 'bar')), '1 bar')
		self.assertEqual(repr(Entry(1, 'bar')), 'Entry(1, {0})'.format(repr('bar')))
		entry = Entry(1, 'bar')
		entry.is_resume = True
		self.assertEqual(repr(entry), 'Entry(1, {0}, is_resume=True)'.format(repr('bar')))
		entry = Entry(1, 'bar')
		entry.is_stop = True
		self.assertEqual(repr(entry), 'Entry(1, {0}, is_stop=True)'.format(repr('bar')))

class TestTaskStat(unittest.TestCase):
	def should_compare_entries(self):
		self.assertEqual(Stat(1, 2, 'foo'), Stat(1, 2, 'foo'))
		self.assertEqual(Stat(1, 2, 'foo'), Stat(2, 3, 'foo'))
		self.assertNotEqual(Stat(1, 2, 'bar'), Stat(1, 3, 'bar'))
		self.assertTrue(Stat(1, 2, 'bar') == Stat(2, 3, 'bar'))
		self.assertFalse(Stat(1, 2, 'bar') != Stat(2, 3, 'bar'))
		self.assertFalse(Stat(1, 2, 'bar') == Stat(2, 4, 'bar'))
		self.assertTrue(Stat(1, 2, 'bar') != Stat(1, 3, 'bar'))
	def should_repr_entries(self):
		self.assertEqual(str(Stat(1, 2, 'bar')), '1 bar')
		self.assertEqual(repr(Stat(1, 2, 'bar')), 'Stat(1, 2, {0})'.format(repr('bar')))

class TestTaskWarrior(unittest.fs.TestCase):
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[clckwrkbdgr.taskwarrior, clckwrkbdgr.taskwarrior._base])
		taskwarrior_dir = xdg.save_data_path('taskwarrior')
		if not taskwarrior_dir.exists():
			self.fs.create_dir(str(taskwarrior_dir))
		taskwarrior_state_dir = xdg.save_state_path('taskwarrior')
		if not taskwarrior_state_dir.exists():
			self.fs.create_dir(six.text_type(taskwarrior_state_dir))
	def should_return_current_task(self):
		task = TaskWarrior()
		self.assertIsNone(task.get_current_task())
		task.start('foo')
		self.assertEqual(task.get_current_task(), 'foo')
		task.start('bar')
		self.assertEqual(task.get_current_task(), 'bar')
		task.stop()
		self.assertIsNone(task.get_current_task())
	def should_start_task(self):
		task = TaskWarrior()
		self.assertIsNone(task.get_current_task())
		task.start('foo')
		self.assertEqual(task.get_current_task(), 'foo')
	def should_stop_task(self):
		task = TaskWarrior()
		self.assertIsNone(task.get_current_task())
		task.start('foo')
		self.assertEqual(task.get_current_task(), 'foo')
		task.stop()
		self.assertIsNone(task.get_current_task())
	def should_resume_stopped_task(self):
		task = TaskWarrior()
		self.assertFalse(task.start())
		self.assertIsNone(task.get_current_task())

		task.start('foo')
		task.stop()
		self.assertTrue(task.start())
		self.assertEqual(task.get_current_task(), 'foo')
	def should_ignore_duplicate_task_and_time_entries(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		self.assertEqual([_.title for _ in task.get_history()], ['foo'])
	def should_slightly_shift_start_time_for_consequent_entries_with_the_same_time(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.get_history()], [
			('foo', datetime.time(8, 0)),
			('bar', datetime.time(8, 0, 0, 1)),
			])
	def should_list_task_history(self):
		task = TaskWarrior()
		task.start('foo')
		task.start('bar')
		task.stop()
		self.assertEqual([_.title for _ in task.get_history()], ['foo', 'bar', None])
	def should_filter_task_history_by_datetime(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 20, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 45, 0))
		task.start('baz', now=datetime.datetime(2020, 12, 31, 9, 40, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 10, 20, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 12, 1, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			start_datetime=datetime.datetime(2020, 12, 31, 8, 10, 0),
			stop_datetime=datetime.datetime(2020, 12, 31, 11, 10, 0),
			)], [
			('bar', datetime.time(8, 20)),
			(None, datetime.time(8, 45)),
			('baz', datetime.time(9, 40)),
			(None, datetime.time(10, 20)),
			])
	def should_filter_out_duplicated_stop_resume_events(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 5))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 5))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 5, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 5, 3))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			)], [
			('foo', datetime.time(8, 0)),
			('foo', datetime.time(8, 1)),
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 3)),
			('foo', datetime.time(8, 3, 5)),
			(None, datetime.time(8, 4)),
			('bar', datetime.time(8, 5)),
			('bar', datetime.time(8, 5, 3)),
			])
	def should_filter_history_for_breaks(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 5, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			only_breaks=True,
			)], [
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 3)),
			])

		task = TaskWarrior()
		task.config.taskfile.write_bytes(b'')
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			only_breaks=True,
			)], [
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 3)),
			])
	def should_squeeze_consequent_break_events(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 5, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 6, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			squeeze_breaks=True,
			)], [
			('foo', datetime.time(8, 0)),
			('foo', datetime.time(8, 1)),
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 5)),
			('bar', datetime.time(8, 6)),
			])

		task = TaskWarrior()
		task.config.taskfile.write_bytes(b'')
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 5, 0))
		task.start('bar', now=datetime.datetime(2020, 12, 31, 8, 6, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			squeeze_breaks=True,
			only_breaks=True,
			)], [
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 5)),
			])

		task = TaskWarrior()
		task.config.taskfile.write_bytes(b'')
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 5, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			squeeze_breaks=True,
			only_breaks=True,
			)], [
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 5)),
			])

		task = TaskWarrior()
		task.config.taskfile.write_bytes(b'')
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		self.assertEqual([(_.title, _.datetime.time()) for _ in task.filter_history(
			squeeze_breaks=True,
			only_breaks=True,
			)], [
			(None, datetime.time(8, 2)),
			('foo', datetime.time(8, 3)),
			])
	def should_not_consider_consequent_tasks_as_resume(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 0, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2020, 12, 31, 8, 3, 0))
		task.stop(now=datetime.datetime(2020, 12, 31, 8, 4, 0))
		task.start('foo', now=datetime.datetime(2020, 12, 31, 8, 5, 0))
		history = list(task.get_history())
		self.assertFalse(history[0].is_resume)
		self.assertFalse(history[1].is_resume)
		self.assertTrue(history[2].is_stop)
		self.assertTrue(history[3].is_resume)
		self.assertTrue(history[4].is_stop)
		self.assertTrue(history[5].is_resume)
	def should_use_custom_aliases_for_stop_and_resume(self):
		task = TaskWarrior(Config(
			resume_alias='UNLOCK',
			stop_alias='LOCK',
			))

		task.config.taskfile.write_text(six.text_type('\n'.join([
			'{0} foo'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat()),
			'{0} LOCK'.format(datetime.datetime(2021, 12, 31, 8, 10, 0).isoformat()),
			'{0} UNLOCK'.format(datetime.datetime(2021, 12, 31, 8, 30, 0).isoformat()),
			]) + '\n'))
		history = list(task.get_history())
		self.assertEqual(len(history), 3)
		self.assertFalse(history[0].is_resume)
		self.assertFalse(history[0].is_stop)
		self.assertFalse(history[1].is_resume)
		self.assertTrue(history[1].is_stop)
		self.assertTrue(history[2].is_resume)
		self.assertFalse(history[2].is_stop)
		self.assertEqual(task.get_current_task(), 'foo')

		task.config.taskfile.write_text(six.text_type('\n'.join([
			'{0} foo'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat()),
			'{0} LOCK'.format(datetime.datetime(2021, 12, 31, 8, 10, 0).isoformat()),
			'{0} UNLOCK'.format(datetime.datetime(2021, 12, 31, 8, 30, 0).isoformat()),
			'{0}'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat()),
			'{0} foo'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat()),
			]) + '\n'))
		history = list(task.get_history())
		self.assertEqual(len(history), 5)
		self.assertFalse(history[0].is_resume)
		self.assertFalse(history[0].is_stop)
		self.assertFalse(history[1].is_resume)
		self.assertTrue(history[1].is_stop)
		self.assertTrue(history[2].is_resume)
		self.assertFalse(history[2].is_stop)
		self.assertFalse(history[3].is_resume)
		self.assertTrue(history[3].is_stop)
		self.assertTrue(history[4].is_resume)
		self.assertFalse(history[4].is_stop)
		self.assertEqual(task.get_current_task(), 'foo')

		task.config.taskfile.write_text(six.text_type('\n'.join([
			'{0} foo'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat()),
			'{0} LOCK'.format(datetime.datetime(2021, 12, 31, 8, 10, 0).isoformat()),
			'{0} UNLOCK'.format(datetime.datetime(2021, 12, 31, 8, 30, 0).isoformat()),
			'{0} bar'.format(datetime.datetime(2021, 12, 31, 8, 40, 0).isoformat()),
			'{0} foo'.format(datetime.datetime(2021, 12, 31, 8, 50, 0).isoformat()),
			]) + '\n'))
		history = list(task.get_history())
		self.assertEqual(len(history), 5)
		self.assertFalse(history[0].is_resume)
		self.assertFalse(history[0].is_stop)
		self.assertFalse(history[1].is_resume)
		self.assertTrue(history[1].is_stop)
		self.assertIsNone(history[1].title)
		self.assertTrue(history[2].is_resume)
		self.assertFalse(history[2].is_stop)
		self.assertEqual(history[2].title, 'foo')
		self.assertFalse(history[3].is_resume)
		self.assertFalse(history[3].is_stop)
		self.assertEqual(history[3].title, 'bar')
		self.assertFalse(history[4].is_resume)
		self.assertFalse(history[4].is_stop)
		self.assertEqual(history[4].title, 'foo')
		self.assertEqual(task.get_current_task(), 'foo')
	def should_use_custom_separator_for_entry_tuple(self):
		task = TaskWarrior(Config(separator='__'))
		task.start('foo')
		task.start('bar')
		self.assertTrue('__foo' in task.config.taskfile.read_text())
		task.stop()
		self.assertEqual([_.title for _ in task.get_history()], ['foo', 'bar', None])
	def should_try_to_guess_separator_for_line(self):
		task = TaskWarrior(Config(separator='__'))
		task.config.taskfile.write_text(six.text_type('\n'.join([
			'{0}__foo'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat()),
			'{0}\tbar with space'.format(datetime.datetime(2021, 12, 31, 8, 10, 0).isoformat()),
			'{0} baz with space'.format(datetime.datetime(2021, 12, 31, 8, 20, 0).isoformat()),
			'{0}'.format(datetime.datetime(2021, 12, 31, 8, 30, 0).isoformat()),
			]) + '\n'))
		self.assertEqual([_.title for _ in task.get_history()], ['foo', 'bar with space', 'baz with space', None])
	def should_recognize_isodate_without_msecs(self):
		task = TaskWarrior(Config(separator='__'))
		task.config.taskfile.write_text(six.text_type('\n'.join([
			'{0}\tfoo'.format(datetime.datetime(2021, 12, 31, 8, 0, 0).isoformat().split('.', 1)[0]),
			'{0}\tbar'.format(datetime.datetime(2021, 12, 31, 8, 10, 0).isoformat()),
			'{0}'.format(datetime.datetime(2021, 12, 31, 8, 30, 0).isoformat()),
			]) + '\n'))
		self.assertEqual([_.title for _ in task.get_history()], ['foo', 'bar', None])
	def should_collect_entries_to_passed_stats(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2021, 12, 31, 8, 2, 0))
		task.stop(now=datetime.datetime(2021, 12, 31, 8, 5, 0))
		task.start(now=datetime.datetime(2021, 12, 31, 8, 7, 0))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 8, 0))

		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(2, 'foo'),
				(3, 'bar'),
				(1, 'bar'),
				(22, 'foo'),
				])
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			start_datetime=datetime.datetime(2021, 12, 31, 7, 30, 0),
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(2, 'foo'),
				(3, 'bar'),
				(1, 'bar'),
				(22, 'foo'),
				])
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			start_datetime=datetime.datetime(2021, 12, 31, 8, 1, 0),
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(1, 'foo'),
				(3, 'bar'),
				(1, 'bar'),
				(22, 'foo'),
				])
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			start_datetime=datetime.datetime(2021, 12, 31, 8, 1, 0),
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 6, 0),
			)], [
				(1, 'foo'),
				(3, 'bar'),
				])
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			start_datetime=datetime.datetime(2021, 12, 31, 8, 1, 0),
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 4, 0),
			)], [
				(1, 'foo'),
				(2, 'bar'),
				])
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			start_datetime=datetime.datetime(2021, 12, 31, 8, 2, 0),
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 4, 0),
			)], [
				(2, 'bar'),
				])
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			start_datetime=datetime.datetime(2021, 12, 31, 8, 3, 0),
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 4, 0),
			)], [
				(1, 'bar'),
				])

		task.stop(now=datetime.datetime(2021, 12, 31, 8, 10, 0))
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(2, 'foo'),
				(3, 'bar'),
				(1, 'bar'),
				(2, 'foo'),
				])
	def should_squeeze_consequent_stats(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2021, 12, 31, 8, 2, 0))
		task.stop(now=datetime.datetime(2021, 12, 31, 8, 5, 0))
		task.start(now=datetime.datetime(2021, 12, 31, 8, 7, 0))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 8, 0))

		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			squeeze=True,
			)], [
				(2, 'foo'),
				(3, 'bar'),
				(1, 'bar'),
				(22, 'foo'),
				])

		task.rewrite_history(
				datetime.datetime(2021, 12, 31, 8, 5, 0),
				datetime.datetime(2021, 12, 31, 8, 7, 0),
				['bar', 'bar']
				)
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			squeeze=True,
			)], [
				(2, 'foo'),
				(6, 'bar'),
				(22, 'foo'),
				])

		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 10, 0))
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.get_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			squeeze=True,
			)], [
				(2, 'foo'),
				(6, 'bar'),
				(22, 'foo'),
				])
	def should_accumulate_stats(self):
		task = TaskWarrior()
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2021, 12, 31, 8, 2, 0))
		task.stop(now=datetime.datetime(2021, 12, 31, 8, 5, 0))
		task.start(now=datetime.datetime(2021, 12, 31, 8, 7, 0))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 8, 0))

		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.accumulate_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(4, 'bar'),
				(24, 'foo'),
				])

		task.rewrite_history(
				datetime.datetime(2021, 12, 31, 8, 5, 0),
				datetime.datetime(2021, 12, 31, 8, 7, 0),
				['bar', 'bar']
				)
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.accumulate_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(6, 'bar'),
				(24, 'foo'),
				])

		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 10, 0))
		self.assertEqual([(_.passed.total_seconds()/60, _.title) for _ in task.accumulate_stats(
			stop_datetime=datetime.datetime(2021, 12, 31, 8, 30, 0),
			)], [
				(6, 'bar'),
				(24, 'foo'),
				])
	def should_rewrite_task_history_automatically(self):
		task = TaskWarrior(Config(separator='__'))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2021, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2021, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2021, 12, 31, 8, 3, 0))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 4, 0))

		with self.assertRaises(RuntimeError):
			task.rewrite_history(
					datetime.datetime(2021, 12, 31, 8, 2, 0),
					datetime.datetime(2021, 12, 31, 8, 3, 0),
					['baz', 'baz', 'excessive'],
					)
		with self.assertRaises(RuntimeError):
			task.rewrite_history(
					datetime.datetime(2021, 12, 31, 8, 2, 0),
					datetime.datetime(2021, 12, 31, 8, 3, 0),
					['not enough values'],
					)

		task.rewrite_history(
				datetime.datetime(2021, 12, 31, 8, 2, 0),
				datetime.datetime(2021, 12, 31, 8, 3, 0),
				['baz', 'baz'],
				)
		self.assertEqual([_.title for _ in task.get_history()], [
			'foo', 'bar',
			'baz', 'baz',
			'foo',
			])
		task.rewrite_history(
				datetime.datetime(2021, 12, 31, 8, 2, 0),
				datetime.datetime(2021, 12, 31, 8, 3, 0),
				['foo', None],
				)
		self.assertEqual([_.title for _ in task.get_history()], [
			'foo', 'bar',
			'foo', None,
			'foo',
			])
	def should_rewrite_task_history_with_fill_value(self):
		task = TaskWarrior(Config(separator='__'))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 0, 0))
		task.start('bar', now=datetime.datetime(2021, 12, 31, 8, 1, 0))
		task.stop(now=datetime.datetime(2021, 12, 31, 8, 2, 0))
		task.start(now=datetime.datetime(2021, 12, 31, 8, 3, 0))
		task.start('foo', now=datetime.datetime(2021, 12, 31, 8, 4, 0))

		task.rewrite_history(
				datetime.datetime(2021, 12, 31, 8, 2, 0),
				datetime.datetime(2021, 12, 31, 8, 3, 0),
				['foo'],
				fill_value='baz'
				)
		self.assertEqual([_.title for _ in task.get_history()], [
			'foo', 'bar',
			'foo', 'baz',
			'foo',
			])
	@mock.patch('subprocess.call', side_effect=[0])
	def should_fix_task_history(self, subprocess_call):
		task = TaskWarrior()
		self.assertTrue(task.fix_history())
		subprocess_call.assert_has_calls([
			mock.call([os.environ.get('EDITOR', 'vi'), str(task.config.taskfile)]),
			])
