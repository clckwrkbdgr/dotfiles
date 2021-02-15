#!/usr/bin/env python
from __future__ import print_function
import os, sys, shutil, subprocess
import getpass
import datetime
import logging
import functools, contextlib
import email.parser
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.utils, clckwrkbdgr.fs

MAILBOX = Path(os.environ.get('MAILPATH', Path('/var/mail')/getpass.getuser()))
MAILBOX_BAK = xdg.save_cache_path()/'mbox.{0}'.format(os.getpid())

def mail_command(commands):
	MAIL_COMMAND = ['mail', '-N']
	p = subprocess.Popen(MAIL_COMMAND, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	_, errors = p.communicate('\n'.join(commands).encode('utf-8', 'replace'))
	if errors:
		logging.error(errors)
	return 0 == p.wait()

def run_custom_filter(command, filename):
	""" Runs custom filter command on given file.
	Command should take filename as $1 and return non-zero if file should be removed.

	Returns True if mail file should be left untouched,
	otherwise False if it should be removed.
	"""
	try:
		return 0 == subprocess.call([command, str(filename)])
	except Exception as e:
		logging.exception('Failed to run custom filter.')
		return True

def save_mail(index, destdir, custom_filters=None):
	destdir = Path(destdir)
	custom_filters = custom_filters or []

	mail_file = Path(str(index))
	if mail_file.exists():
		os.unlink(str(mail_file))
	if not mail_command(["save {index}".format(index=index), 'delete {index}'.format(index=index)]):
		logging.error("Cannot save first message.")
		return False
	if not mail_file.exists():
		logging.error("Cannot save first message.")
		return False
	try:
		try:
			eml = email.parser.BytesHeaderParser().parsebytes(mail_file.read_bytes())
		except AttributeError: # pragma: no cover -- py2 compatibility
			eml = email.parser.Parser().parsestr(mail_file.read_bytes().decode('utf-8', 'replace'), headersonly=True)
		for command in custom_filters:
			if not run_custom_filter(command, mail_file):
				os.unlink(str(mail_file))
				break
		else:
			name = eml['Subject'] or 'mail.{0}.{1}'.format(os.getpid(), datetime.datetime.now().isoformat())
			name = clckwrkbdgr.fs.make_valid_filename(name)
			destfile = clckwrkbdgr.fs.make_unique_filename(destdir/name)
			destdir.mkdir(parents=True, exist_ok=True)
			os.rename(str(mail_file), str(destfile))
	except:
		logging.exception('Failed to process saved mail file {0}. Backup of original mbox is stored at {1}'.format(mail_file, MAILBOX_BAK))
		return False
	return True

import click

def ensure_single_instance(f):
	@functools.wraps(f)
	def _actual(*args, **kwargs):
		pid_file = xdg.save_runtime_path()/'mail2file.pid'
		if pid_file.exists():
			pid = int(pid_file.read_text().strip())
			try:
				os.kill(pid, 0)
				return True # Already running another instance.
			except OSError:
				pass
		pid_file.write_text(str(os.getpid()))
		try:
			return f(*args, **kwargs)
		finally:
			os.unlink(str(pid_file))
	return _actual

@click.command()
@click.argument('destdir')
@click.option('--filter', 'custom_filters', multiple=True, help='Custom filters for mail messages. Each command should take single argument (file name, mbox format) and return EXIT_FAILURE (non-zero) in case if file should be removed. Filters are applied in order of specification. Filter command can alter file content.')
@clckwrkbdgr.utils.exits_with_return_value
@ensure_single_instance
def main(destdir, custom_filters=None):
	""" Saves Unix mailbox to a set of files.

	Destination directory will be created if does not exist.
	"""
	if not MAILBOX.exists():
		return True
	if MAILBOX.stat().st_size == 0:
		return True
	repeats = 1000
	try:
		shutil.copy(str(MAILBOX), str(MAILBOX_BAK))
	except IOError as e:
		if e.errno == 28: # No space left on device.
			return True # Silently ignore to not produce another cron mail.
		raise
	TEMPDIR = xdg.save_cache_path('mail.{0}'.format(os.getpid()))
	os.chdir(str(TEMPDIR))
	while MAILBOX.stat().st_size != 0:
		if not save_mail(1, destdir, custom_filters=custom_filters):
			return False
		repeats -= 1
		if repeats <= 0:
			print("Loop detected: cannot save first mail, stopping after 1000 iterations.", file=sys.stderr)
			return False
	try:
		os.chdir('/')
		shutil.rmtree(str(TEMPDIR))
	except OSError as e:
		logging.exception('Failed to remove temp dir.')
	os.unlink(str(MAILBOX_BAK))
	return True

if __name__ == '__main__':
	main()
