import os, subprocess, shutil
import clckwrkbdgr.backup
import logging

class SevenZipArchiver: # pragma: no cover -- TODO uses direct access to FS and processes.
	def __init__(self, context):
		self.context = context
	def perform(self):
		backup_dir = self.context.root
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
				subprocess.check_call(list(map(str, backup_command)), shell=True)
		except Exception as e:
			logging.error(e)
			return False
		return True
	def check(self):
		backup_dir = self.context.root
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
			output = output.decode('utf-8', 'replace').splitlines()
			# New 7-Zip prints date/time and sizes in listing, which are updates very often.
			# It leads for large diffs in backup logs every time.
			# Need only Name.
			processed_lines = []
			expected_header = '   Date      Time    Attr         Size   Compressed  Name'.strip().split()
			strip_size = None
			for line in output:
				if line.strip().split() == expected_header:
					strip_size = line.find(expected_header[-1]) - 1
				if strip_size:
					line = line[strip_size:]
				processed_lines.append(line)
		except Exception as e:
			logging.error(e)
			return False

		logging.debug('+{0}'.format(' '.join(map(str, list_command))))
		try:
			with self.context.password.disclosed():
				subprocess.check_call(list(map(str, list_command)), shell=True)
		except Exception as e:
			logging.error(e)
			return False
		return True
	def deploy(self):
		backup_archive = self.context.tempdir/'{0}.zip'.format(self.context.name)
		for location in self.context.destinations:
			logging.debug(location)
			shutil.copy(str(backup_archive), str(location))
		return True
