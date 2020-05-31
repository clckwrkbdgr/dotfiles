#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import os, sys, shutil, subprocess
import getpass
import argparse
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path

MAILBOX = Path(os.environ.get('MAILPATH', Path('/var/mail')/getpass.getuser()))
MAILBOX_BAK = Path.home()/'.cache'/'mbox.{0}'.format(os.getpid()) # TODO xdg or tmp?
TEMPDIR = Path.home()/'.cache'/'mail.{0}'.format(os.getpid()) # TODO xdg or tmp?

def mail_command(commands):
	MAIL_COMMAND = ['mail', '-N']
	p = subprocess.Popen(MAIL_COMMAND, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	_, errors = p.communicate('\n'.join(commands).encode('utf-8', 'replace'))
	if errors:
		print(errors)
	return 0 == p.wait()

def get_header(mbox):
	for line in mbox.splitlines():
		if line.startswith('Subject: '):
			return line.split(' ', 1)[-1].replace('/', '_') # TODO move it out of here and make check_os_file_name(filename)
	return None

def print_body(mbox):
	body_start = mbox.find('\n\n')
	if body_start < 0:
		return None
	return mbox[body_start+1:]

def run_custom_filter(command, filename):
	return 0 == subprocess.call([command, str(filename)])

def save_mail(index, destdir, custom_filters=None):
	destdir = Path(destdir)
	custom_filters = custom_filters or []

	TEMPDIR.mkdir(parents=True, exist_ok=True)
	os.chdir(str(TEMPDIR))
	mail_file = Path(str(index))
	if mail_file.exists():
		shutil.remove(str(mail_file))
	if not mail_command(["save {index}".format(index=index), 'delete {index}'.format(index=index)]):
		print("Cannot save first message.", file=sys.stderr)
		return False
	if not mail_file.exists():
		print("Cannot save first message.", file=sys.stderr)
		return False
	content = mail_file.read_bytes().decode('utf-8', 'replace')
	orig_header = get_header(content)
	header = orig_header
	counter = 0
	while (destdir/header).exists():
		header = "{0}_{1}".format(orig_header, counter)
		counter += 1
	for command in custom_filters:
		if not run_custom_filter(command, mail_file):
			shutil.remove(str(mail_file))
			break
	else:
		destdir.mkdir(parents=True, exist_ok=True)
		os.rename(str(mail_file), str(destdir/header))
	os.chdir('/')
	try:
		shutil.rmtree(str(TEMPDIR))
	except OSError as e:
		print(e, file=sys.stderr)
	return True

def main(destdir, custom_filters=None):
	if not MAILBOX.exists():
		return True
	if MAILBOX.stat().st_size == 0:
		return True
	repeats = 1000
	shutil.copy(str(MAILBOX), str(MAILBOX_BAK))
	while MAILBOX.stat().st_size != 0:
		save_mail(1, destdir, custom_filters=custom_filters)
		repeats -= 1
		if repeats <= 0:
			print("Loop detected: cannot save first mail, stopping after 1000 iterations.", file=sys.stderr)
			return False
	os.remove(str(MAILBOX_BAK))
	return True

if __name__ == '__main__': # TODO click
	parser = argparse.ArgumentParser(description='Saves Unix mailbox to a set of files.')
	parser.add_argument('destdir', help='Destination directory. Will be created if does not exist.')
	parser.add_argument('--filter', nargs='+', help='Custom filters for mail messages. Each command should take single argument (file name, mbox format) and return EXIT_FAILURE (non-zero) in case if file should be removed. Filters are applied in order of specification. Filter command can alter file content.')
	settings = parser.parse_args()
	if not main(settings.destdir, custom_filters=settings.filter):
		sys.exit(1)
