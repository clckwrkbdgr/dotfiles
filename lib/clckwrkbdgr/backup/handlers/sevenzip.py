import os, sys, subprocess, shutil
import platform, fnmatch, re
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
			logging.exception('Failed to run backup command {0}:'.format(backup_command))
			return False
		except Exception as e:
			logging.exception('Failed to run backup command {0}:'.format(backup_command))
			return False
		logging.debug('Everything is Ok')
		return True
	def check(self):
		backup_dir = os.path.abspath(str(self.context.root))
		backup_archive = self.context.tempdir/'{0}.zip'.format(self.context.name)
		integrity_command = [self.context.zip_path, 't', str(backup_archive)]
		if self.context.password:
			integrity_command.append(clckwrkbdgr.backup.PasswordArg(self.context.password))
		list_command = [self.context.zip_path, 'l', '-sccUTF-8', str(backup_archive)]
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
			logging.exception('Failed to run check command {0}:'.format(integrity_command))
			return False
		except Exception as e:
			logging.exception('Failed to run check command {0}:'.format(integrity_command))
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
			encoding = 'utf-8'
			encoding_trans = str.maketrans(*self.context.encoding_translation)
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
					filename = filename.translate(encoding_trans)
					stored_files.append(os.path.join(
						os.path.dirname(os.path.abspath(str(self.context.root))), # Name from backup listing should already include root dirname.
						filename,
						))
			existing_files = []
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
			logging.exception('Failed to run list command {0}:'.format(list_command))
			return False
		except Exception as e:
			logging.exception('Failed to verify backup listing:')
			return False

		try:
			if self.context.max_archive_size is not None and backup_archive.stat().st_size > self.context.max_archive_size:
				list_command = [self.context.zip_path, 'l', str(backup_archive)]
				output = subprocess.check_output(list(map(str, list_command)), shell=True)
				output = output.decode('utf-8', 'replace').splitlines()
				output = sort_backup_size(output)
				logging.warning('WARNING: Backup archive size is greater than allowed: {0} > {1}'.format(backup_archive.stat().st_size, self.context.max_archive_size))
				sys.stderr.write('\n'.join(output) + '\n')
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.output.decode('utf-8', 'replace'))
			logging.exception('Failed to run list command {0}:'.format(list_command))
			return False
		except Exception as e:
			logging.exception('Failed to check backup size:')
			return False

		logging.debug('Everything is Ok')
		return True
	def deploy(self):
		backup_archive = self.context.tempdir/'{0}.zip'.format(self.context.name)
		for location in self.context.destinations:
			logging.debug(location)
			shutil.copy(str(backup_archive), str(location))
		return True

def split_sections(line): # pragma: no cover -- TODO
	sections = re.split(r'(\S+)', line)
	if len(sections) % 2 != 0 and sections[-1] == '':
		sections.pop(-1)
	sections = list(map(''.join, zip(sections[::2], sections[1::2])))
	return sections

class BackupSizeNode(object): # pragma: no cover -- TODO
	def __init__(self, line, name):
		self.line = line
		self.name = name
		self.size = 0
		self.compressed_size = 0
	def add_size(self, size, compressed_size=0):
		self.size += size
		self.compressed_size += compressed_size
	def as_string(self):
		sections = split_sections(self.line)
		sections[3] = str(self.size).rjust(len(sections[3]))
		sections[4] = str(self.compressed_size).rjust(len(sections[4]))
		return ''.join(sections)

def sort_backup_size(lines): # pragma: no cover -- TODO
	""" Accepts iterable of lines (header -> file listing -> footer),
	returns list of lines (header -> sorted and processed listing -> footer).
	Headers and footers are not changed.
	"""
	header, listing, footer = [], None, None
	for line in lines:
		if listing is None:
			header.append(line)
			if line.startswith('----'):
				listing = []
		elif footer is None:
			if line.startswith('----'):
				footer = [line]
			else:
				listing.append(line)
		else:
			footer.append(line)

	listing = sorted(listing, key=lambda line: line.split(None, 5)[-1].split(os.sep))

	fixed_listing = []
	stack = []
	for line in listing:
		if line == 'warning:  Converted unicode filename too long--truncating.':
			continue
		parts = line.split(None, 5)
		try:
			size = int(parts[3])
		except Exception as e:
			logging.warning("sort_backup_size: cannot parse line: {0}:".format(e) + repr(line))
			continue
		try:
			compressed_size = int(parts[4])
		except Exception as e:
			logging.warning("sort_backup_size: cannot parse line: {0}:".format(e) + repr(line))
			continue
		name = parts[-1]
		for entry in reversed(stack):
			if name.startswith(entry.name):
				entry.add_size(size, compressed_size)
		done = []
		for entry in reversed(stack):
			if not name.startswith(entry.name.rstrip('/')):
				done.append(entry)
		if done:
			stack = [entry for entry in stack if entry not in done]
			for entry in done:
				fixed_listing.append(entry)
		entry = BackupSizeNode(line, name)
		entry.size = size
		entry.compressed_size = compressed_size
		stack.append(entry)
	for entry in reversed(stack):
		fixed_listing.append(entry)

	sorted_listing = [entry.as_string() for entry in sorted(fixed_listing, key=lambda x: (x.size, -len(x.line)), reverse=True)]

	return header + sorted_listing + footer
