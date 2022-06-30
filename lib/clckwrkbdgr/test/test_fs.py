from clckwrkbdgr import unittest
from clckwrkbdgr.unittest import mock
import os
import clckwrkbdgr.fs
from clckwrkbdgr.collections import dotdict
try: # pragma: no cover
	import pathlib2 as pathlib
	from pathlib2 import Path
except ImportError: # pragma: no cover
	import pathlib
	from pathlib import Path

@mock.patch('os.getcwd', return_value='old')
@mock.patch('os.chdir')
class TestPathUtils(unittest.TestCase):
	def should_change_current_dir(self, mock_getcwd, mock_chdir):
		with clckwrkbdgr.fs.CurrentDir('new'):
			self.assertEqual(os.chdir.call_args, (('new',),))
		self.assertEqual(os.chdir.call_args, (('old',),))
	def should_use_path_object_to_change_current_dir(self, mock_getcwd, mock_chdir):
		with clckwrkbdgr.fs.CurrentDir(Path('new')):
			self.assertEqual(os.chdir.call_args, (('new',),))
		self.assertEqual(os.chdir.call_args, (('old',),))

class TestFSUtils(unittest.TestCase):
	def should_create_valid_filename(self):
		self.assertEqual(clckwrkbdgr.fs.make_valid_filename('name/with/slashes'), 'name_with_slashes')
	@mock.patch(pathlib.__name__ + '.Path.exists', side_effect=(True, True, True, False))
	def should_create_unique_name(self, *mocks):
		self.assertEqual(clckwrkbdgr.fs.make_unique_filename('foo.bar'), Path('foo.2.bar'))
	@mock.patch('os.path.exists', side_effect=(False, False, True, True, False, True, True, True))
	@mock.patch('os.stat', side_effect=(dotdict(st_mtime=2), dotdict(st_mtime=2), dotdict(st_mtime=3), dotdict(st_mtime=3), dotdict(st_mtime=3)))
	def should_react_to_modified_files(self, *mocks):
		events = []
		def action():
			events.append('.')
		watcher = clckwrkbdgr.fs.FileWatcher('filename', action)
		self.assertEqual(events, [])
		self.assertFalse(watcher.check()) # Still does not exist.
		self.assertEqual(events, [])
		self.assertTrue(watcher.check()) # Was created.
		self.assertEqual(events, ['.'])
		self.assertFalse(watcher.check()) # Was not changed.
		self.assertEqual(events, ['.'])
		self.assertFalse(watcher.check()) # Was removed.
		self.assertEqual(events, ['.'])
		self.assertTrue(watcher.check()) # Was re-created.
		self.assertEqual(events, ['.', '.'])

		watcher = clckwrkbdgr.fs.FileWatcher('filename', action)
		self.assertFalse(watcher.check()) # Exists but not modified.

class TestSearchForFiles(unittest.fs.TestCase):
	FILES = {
			'/search_test/filename',
			'/search_test/module.pyc',
			'/search_test/subdir/subfile',
			'/search_test/subdir/other_file',
			'/search_test/other_dir/other_file',
			}
	def setUp(self):
		self.setUpPyfakefs(modules_to_reload=[clckwrkbdgr.fs])
		for filename in self.FILES:
			self.fs.create_file(filename)
	def should_list_all_files_unconditionally(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/')), set(map(Path, self.FILES)))
	def should_list_files_under_current_dir(self):
		os.chdir('/search_test/subdir')
		self.assertEqual(set(clckwrkbdgr.fs.find('.')), {
			Path('subfile'),
			Path('other_file'),
			})
	def should_exclude_dirs(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_dir_names=['subdir'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/other_dir/other_file'),
			})
	def should_exclude_dirs_by_wildcard(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_dir_wildcards=['*_dir'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/subdir/subfile'),
			Path('/search_test/subdir/other_file'),
			})
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_dir_wildcards=['*dir'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			})
	def should_exclude_files(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_file_names=['other_file'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/subdir/subfile'),
			})
	def should_exclude_files_by_wildcard(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_file_wildcards=['*file'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			})
	def should_exclude_files_by_wildcard_in_relative_root(self):
		os.chdir('/search_test/')
		self.assertEqual(set(clckwrkbdgr.fs.find('.',
			exclude_file_wildcards=['/search_test/subdir/sub*'],
			)), {
			Path('filename'),
			Path('module.pyc'),
			Path('subdir/other_file'),
			Path('other_dir/other_file'),
			})
	def should_exclude_files_by_wildcard_in_abs_root(self):
		os.chdir('/search_test/')
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_file_wildcards=['/search_test/subdir/sub*'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/subdir/other_file'),
			Path('/search_test/other_dir/other_file'),
			})
	def should_exclude_both_dirs_and_files(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_names=['subdir'],
			exclude_wildcards=['other*'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			})
	def should_exclude_by_extensions(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			exclude_extensions=['.pyc'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/subdir/subfile'),
			Path('/search_test/subdir/other_file'),
			Path('/search_test/other_dir/other_file'),
			})
	def should_yield_dirs_as_well(self):
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			handle_dirs=True,
			)), {
			Path('/search_test/'),
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/subdir'),
			Path('/search_test/subdir/subfile'),
			Path('/search_test/subdir/other_file'),
			Path('/search_test/other_dir'),
			Path('/search_test/other_dir/other_file'),
			})
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			handle_dirs=True,
			exclude_dir_names=['subdir'],
			)), {
			Path('/search_test/'),
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/other_dir'),
			Path('/search_test/other_dir/other_file'),
			})
	def should_handle_dirs(self):
		class Handler:
			def __init__(self): self.calls = set()
			def __call__(self, value): self.calls.add(value)

		handler = Handler()
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			handle_dirs=handler,
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/subdir/subfile'),
			Path('/search_test/subdir/other_file'),
			Path('/search_test/other_dir/other_file'),
			})
		self.assertEqual(handler.calls, {
			Path('/search_test/'),
			Path('/search_test/subdir'),
			Path('/search_test/other_dir'),
			})

		handler = Handler()
		self.assertEqual(set(clckwrkbdgr.fs.find('/search_test/',
			handle_dirs=handler,
			exclude_dir_names=['subdir'],
			)), {
			Path('/search_test/filename'),
			Path('/search_test/module.pyc'),
			Path('/search_test/other_dir/other_file'),
			})
		self.assertEqual(handler.calls, {
			Path('/search_test/'),
			Path('/search_test/other_dir'),
			})
