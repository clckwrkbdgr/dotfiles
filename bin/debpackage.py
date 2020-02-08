#!/usr/bin/env python3
import os, sys, shutil
import subprocess, tempfile
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Utility to create Debian package.')
parser.add_argument('--dry', action='store_true', default=False, help='Dry run. Do not execute any actions, just log them.')
parser.add_argument('name', help='Package name.')
parser.add_argument('-v', '--version', required=True, help='Package version.')
parser.add_argument('--maintainer', default=os.environ['USER'], help='Maintaner of the package, usually in form "NAME <name@email>". By default current OS user is picked (name only).')
parser.add_argument('--description', help='Package description (free text).')

parser.add_argument('--bin', dest='bins', nargs='+', default=[], help='Executables to install.')
parser.add_argument('--lib', dest='libs', nargs='+', default=[], help='Libraries to install.')
parser.add_argument('--header', dest='headers', nargs='+', default=[], help='Include headers to install.')
parser.add_argument('--doc', dest='docs', nargs='+', default=[], help='Docs to install.')

parser.add_argument('--build-dir', help='Directory to store intermediate files. Default is within system temp directory.')
parser.add_argument('--dest-dir', help='Directory to store final package. Default is one level up from build-dir.')
parser.add_argument('--arch', help='Package architecture. Default is arch of the current system.')

settings = parser.parse_args()
settings.remove_build_dir = False
if settings.build_dir is None:
	settings.build_dir = tempfile.mkdtemp()
	settings.remove_build_dir = True
settings.build_dir = Path(settings.build_dir)
if not settings.arch:
	settings.arch = subprocess.check_output(['dpkg', '--print-architecture']).decode().strip()

try:
	if settings.build_dir.exists():
		if settings.dry:
			print('[DRY] Removing old build dir')
		else:
			shutil.rmtree(str(settings.build_dir))
	print('Creating build dir...')
	settings.build_dir.mkdir(parents=True, exist_ok=True)

	for binfile in settings.bins:
		dest = settings.build_dir/'usr'/'local'/'bin'/Path(binfile).name
		print('Copying executable: {0}'.format(binfile))
		if not settings.dry:
			subprocess.call(['install', '-D', binfile, str(dest)])
	for lib in settings.libs:
		dest = settings.build_dir/'usr'/'local'/'lib'/Path(lib).name
		dest_version = Path(str(dest) + '.{0}'.format(settings.version))
		print('Copying lib: {0}'.format(lib))
		if not settings.dry:
			subprocess.call(['install', '-D', lib, str(dest_version)])
			os.symlink(dest_version.name, str(dest))
	for header in settings.headers:
		dest = settings.build_dir/'usr'/'local'/'include'/settings.name
		dest_version = Path(str(dest) + '.{0}'.format(settings.version))
		print('Copying header: {0}'.format(header))
		if not settings.dry:
			dest_version.mkdir(parents=True, exist_ok=True)
			subprocess.call(['install', '-Dm0644', header, str(dest_version)])
			if not dest.exists():
				os.symlink(dest_version.name, str(dest))
	for doc in settings.docs:
		dest = settings.build_dir/'usr'/'local'/'share'/'doc'/settings.name
		dest_version = Path(str(dest) + '.{0}'.format(settings.version))
		dest_version.mkdir(parents=True, exist_ok=True)
		print('Copying docs: {0}'.format(doc))
		if not settings.dry:
			try:
				shutil.copy(doc, str(dest_version))
			except IsADirectoryError:
				shutil.copytree(doc, str(dest_version/Path(doc).name))
			if not dest.exists():
				os.symlink(dest_version.name, str(dest))

	print('Creating manifest...')
	debian_dir = settings.build_dir/'DEBIAN'
	package_name = settings.name
	if settings.libs and not settings.bins:
		package_name = 'lib' + package_name
	manifest = [
			'Package: {0}'.format(package_name),
			'Version: {0}'.format(settings.version),
			'Architecture: {0}'.format(settings.arch),
			'Maintainer: {0}'.format(settings.maintainer),
			'Description: {0}'.format(settings.description),
			]
	if settings.dry:
		print('[DRY] Manifest ({0}):'.format(debian_dir/'control'))
		print('\n'.join(manifest))
	else:
		debian_dir.mkdir(parents=True)
		(debian_dir/'control').write_text('\n'.join(manifest) + '\n')

	if settings.dry:
		print('[DRY] {0}'.format(['fakeroot', 'dpkg-deb', '--build', str(settings.build_dir)]))
	else:
		subprocess.call(['fakeroot', 'dpkg-deb', '--build', str(settings.build_dir)])

	if settings.dest_dir:
		print('Moving package...')
		filename = '{name}_{version}_{arch}.deb'.format(
				name=package_name,
				version=settings.version,
				arch=settings.arch,
				)
		if settings.dry:
			print('[DRY] {0} -> {1}'.format(str(settings.build_dir/'..'/filename), settings.dest_dir))
		else:
			shutil.move(str(settings.build_dir/'..'/filename), settings.dest_dir)
	print('Successfully done.')
finally:
	if settings.remove_build_dir:
		try:
			shutil.rmtree(str(settings.build_dir))
		except Exception as e:
			print(e)

