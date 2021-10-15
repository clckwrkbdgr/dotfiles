import os, sys, subprocess, shutil
import platform, fnmatch
import clckwrkbdgr.backup
import logging

class SevenZipArchiver: # pragma: no cover -- TODO uses direct access to FS and processes.
	def __init__(self, context):
		self.context = context
	def perform(self):
		backup_dir = os.path.abspath(str(self.context.root))
		backup_archive = self.context.tempdir/'{0}.zip'.format(self.context.name)

		backup_command = [self.context.zip_path, 'a']
		if self.context.password:
			backup_command.append(clckwrkbdgr.backup.PasswordArg(self.context.password))
		for entry in self.context.exclude:
			backup_command.append('-xr!' + str(entry))
		backup_command += [str(backup_archive), str(backup_dir)]

		logging.debug('+{0}'.format(' '.join(map(str, backup_command))))
		try:
			if backup_archive.exists():
				os.unlink(str(backup_archive))
			with self.context.password.disclosed():
				output = subprocess.check_output(list(map(str, backup_command)), shell=True)
			if b'Everything is Ok' not in output:
				sys.stderr.write(output.decode('utf-8', 'replace'))
				return False
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.output.decode('utf-8', 'replace'))
			logging.error(e)
			return False
		except Exception as e:
			logging.error(e)
			return False
		logging.debug('Everything is Ok')
		return True
	def check(self):
		backup_dir = os.path.abspath(str(self.context.root))
		backup_archive = self.context.tempdir/'{0}.zip'.format(self.context.name)
		integrity_command = [self.context.zip_path, 't', str(backup_archive)]
		if self.context.password:
			integrity_command.append(clckwrkbdgr.backup.PasswordArg(self.context.password))
		list_command = [self.context.zip_path, 'l', str(backup_archive)]
		if self.context.password:
			list_command.append(clckwrkbdgr.backup.PasswordArg(self.context.password))

		logging.debug('+{0}'.format(' '.join(map(str, integrity_command))))
		try:
			with self.context.password.disclosed():
				output = subprocess.check_output(list(map(str, integrity_command)), shell=True)
			if b'Everything is Ok' not in output:
				sys.stderr.write(output.decode('utf-8', 'replace'))
				return False
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.output.decode('utf-8', 'replace'))
			logging.error(e)
			return False
		except Exception as e:
			logging.error(e)
			return False
		logging.debug('Everything is Ok')

		logging.debug('+{0}'.format(' '.join(map(str, list_command))))
		try:
			with self.context.password.disclosed():
				output = subprocess.check_output(list(map(str, list_command)), shell=True)
			# New 7-Zip prints date/time and sizes in listing, which are updates very often.
			# It leads for large diffs in backup logs every time.
			# Need only Name.
			expected_header = '   Date      Time    Attr         Size   Compressed  Name'.strip().split()
			found_splitters = 0
			strip_size = None
			stored_files = []
			encoding = 'cp866' if platform.system() == 'Windows' else 'utf-8'
			for line in output.decode(encoding, 'replace').splitlines():
				if found_splitters == 2:
					break
				if line.strip().split() == expected_header:
					strip_size = line.find(expected_header[-1])
					continue
				if strip_size:
					if not line.replace(' ', '').strip('-'):
						found_splitters += 1
						continue
					filename = line[strip_size:]
					stored_files.append(os.path.join(
						os.path.dirname(os.path.abspath(str(self.context.root))), # Name from backup listing should already include root dirname.
						filename,
						))
			existing_files = []
			encoding_trans = str.maketrans(*self.context.encoding_translation)
			for root, dirnames, filenames in os.walk(os.path.abspath(str(self.context.root))):
				existing_files.append(root)
				dirnames[:] = [dirname
						for dirname in dirnames
						if not any(fnmatch.fnmatch(dirname, pattern) for pattern in self.context.exclude)
						]
				for filename in filenames:
					if any(fnmatch.fnmatch(filename, pattern) for pattern in self.context.exclude):
						continue
					filename = os.path.join(root, filename)
					filename = filename.translate(encoding_trans)
					existing_files.append(filename)
			import difflib
			lists_differ = False
			for line in difflib.unified_diff(sorted(existing_files), sorted(stored_files), lineterm=''):
				lists_differ = True
				sys.stderr.write(line + '\n')
			if lists_differ:
				return False
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.output.decode('utf-8', 'replace'))
			logging.error(e)
			return False
		except Exception as e:
			logging.error(e)
			return False
		logging.debug('Everything is Ok')
		return True
	def deploy(self):
		backup_archive = self.context.tempdir/'{0}.zip'.format(self.context.name)
		for location in self.context.destinations:
			logging.debug(location)
			shutil.copy(str(backup_archive), str(location))
		return True
