""" Utilities for images. """
import os, sys
import tempfile
import contextlib
import subprocess
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

def read_exif_relation_exiftool(filename): # pragma: no cover -- TODO FS/subprocess
	return subprocess.check_output(['exiftool', '-s3', '-relation', str(filename)]).decode('utf-8', 'replace').strip()

def read_exif_relation_webp(filename): # pragma: no cover -- TODO FS/subprocess
	with tempfile.NamedTemporaryFile() as exif:
		try:
			output = subprocess.check_output(['webpmux', '-get', 'exif', str(filename), '-o', exif.name], stderr=subprocess.STDOUT)
			output = output.decode('utf-8', 'replace').splitlines()
			OK_LINES = [
					'Saved file {0} ({1} bytes)'.format(exif.name, os.stat(exif.name).st_size),
					]
			output = [line for line in output if line.strip() not in OK_LINES]
			if output:
				sys.stderr.write('\n'.join(output) + '\n')
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.stdout.decode('utf-8', 'replace'))
			return False
		import csv
		data = list(csv.reader(exif.read().decode('utf-8', 'replace').splitlines()))
		properties = dict(zip(data[0], data[1]))
		return properties['Relation']

def read_exif_relation(filename): # pragma: no cover -- TODO FS/subprocess
	""" Returns value of EXIF::Relation tag (or its analog) for the file
	or None if tag is absent.
	"""
	if Path(filename).suffix == '.webp':
		return read_exif_relation_webp(filename)
	else:
		return read_exif_relation_exiftool(filename)

def write_exif_relation_webp(filename, value): # pragma: no cover -- TODO FS/subprocess
	rc = 0
	with tempfile.NamedTemporaryFile() as exif:
		exif.write(b'Relation\n' + value.encode('utf-8', 'replace') + b'\n')
		exif.flush()
		try:
			output = subprocess.check_output(['webpmux', '-set', 'exif', exif.name, str(filename), '-o', str(filename)], stderr=subprocess.STDOUT)
			output = output.decode('utf-8', 'replace').splitlines()
			OK_LINES = [
					'Saved file {0} ({1} bytes)'.format(filename, os.stat(str(filename)).st_size),
					]
			output = [line for line in output if line.strip() not in OK_LINES]
			if output:
				sys.stderr.write('\n'.join(output) + '\n')
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.stdout.decode('utf-8', 'replace'))
			return False
	return True

@contextlib.contextmanager
def TempRename(filename, new_name): # pragma: no cover -- TODO FS/subprocess
	try:
		os.rename(str(filename), str(new_name))
	except:
		import traceback
		traceback.print_exc()
		yield
		return
	try:
		yield
	finally:
		try:
			os.rename(str(new_name), str(filename))
		except:
			import traceback
			traceback.print_exc()

def write_exif_relation_exiftool(filename, value, already_renamed=False): # pragma: no cover -- TODO FS/subprocess
	try:
		output = subprocess.check_output(['exiftool', '-q', '-overwrite_original', '-relation={0}'.format(value), str(filename)],
			stderr=subprocess.STDOUT)
		output = output.decode('utf-8', 'replace').splitlines()
		OK_WARNINGS = [
				'Warning: [minor] Empty XMP - {0}'.format(filename),
				'Warning: [Minor] Duplicate XMP property: exifEX:BodySerialNumber - {0}'.format(filename),
				'Warning: [Minor] Duplicate XMP property: xmpMM:InstanceID - {0}'.format(filename),
				'Warning: [Minor] Duplicate XMP property: exif:NativeDigest - {0}'.format(filename),
				'Warning: [minor] Ignored empty rdf:Seq list for xmpMM:History - {0}'.format(filename),
				'Warning: Duplicate XMP block created - {0}'.format(filename),
				'Warning: XMP format error (no closing tag for x:xmpmta) - {0}'.format(filename),
				'Saved file {0} ({1} bytes)'.format(filename, os.stat(str(filename)).st_size),
				]
		output = [line for line in output if line.strip() not in OK_WARNINGS]
		if output:
			sys.stderr.write('\n'.join(output) + '\n')
		return True
	except subprocess.CalledProcessError as e:
		if e.output.startswith(b'Error: Not a valid GIF (looks more like a JPEG)'):
			if already_renamed:
				raise
			jpeg_filename = Path(filename).with_suffix('.jpg')
			with TempRename(filename, jpeg_filename):
				return write_exif_relation_exiftool(jpeg_filename, value, already_renamed=True)
		if e.output.startswith(b'Error: Not a valid PNG (looks more like a JPEG)'):
			if already_renamed:
				raise
			jpeg_filename = Path(filename).with_suffix('.jpg')
			with TempRename(filename, jpeg_filename):
				return write_exif_relation_exiftool(jpeg_filename, value, already_renamed=True)
		if e.output.startswith(b'Error: Not a valid JPEG (looks more like a PNG)'):
			if already_renamed:
				raise
			jpeg_filename = Path(filename).with_suffix('.png')
			with TempRename(filename, jpeg_filename):
				return write_exif_relation_exiftool(jpeg_filename, value, already_renamed=True)
		if e.output.startswith(b'Error: Not a valid JPG (looks more like a PNG)'):
			if already_renamed:
				raise
			jpeg_filename = Path(filename).with_suffix('.png')
			with TempRename(filename, jpeg_filename):
				return write_exif_relation_exiftool(jpeg_filename, value, already_renamed=True)
		sys.stderr.write('write_exif_relation_exiftool: {0}'.format(e.output.decode('utf-8', 'replace')))
		return False

def write_exif_relation(filename, value): # pragma: no cover -- TODO FS/subprocess
	""" Updates value of EXIF::Relation tag (or its analog) for the file.
	"""
	if Path(filename).suffix == '.webp':
		return write_exif_relation_webp(filename, value)
	else:
		return write_exif_relation_exiftool(filename, value)

import click

@click.group()
def cli(): # pragma: no cover
	pass

@cli.command('relation')
@click.argument('filenames', nargs=-1)
def print_relation(filenames): # pragma: no cover
	""" Prints values of EXIF::Relation tag (or its analog) to stdout for every given file.
	Files without corresponding tags are silently skipped.
	"""
	for filename in filenames:
		value = read_exif_relation(filename)
		if value:
			print(value)

@cli.command('set_relation')
@click.argument('filename')
@click.argument('value')
def set_relation(filename, value): # pragma: no cover
	""" Updates value of EXIF::Relation tag (or its analog) for given file.
	"""
	return write_exif_relation(filename, value)

if __name__ == '__main__': # pragma: no cover
	cli()
