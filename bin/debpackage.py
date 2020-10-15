#!/usr/bin/env python3
import os, sys, shutil
import subprocess, tempfile
import functools
from pathlib import Path
import click

@functools.lru_cache()
def get_current_arch():
	return subprocess.check_output(['dpkg', '--print-architecture']).decode().strip()

class Package(object):
	def __init__(self, name, version):
		""" Init package with given name and version and default data. """
		self.name = name
		self.version = version
		self.libs = []
		self.bins = []
		self.docs = []
		self.headers = []
		self.arch = get_current_arch()
		self.maintainer = os.environ['USER']
		self.description = ''
	def set_maintainer(self, maintainer):
		""" Maintainer of the package. Default is current OS user. """
		self.maintainer = maintainer
	def set_description(self, description):
		""" Description of the package. Default is none. """
		self.description = description
	def add_libs(self, libs):
		""" Adds libraries to package from iterable. """
		if libs:
			self.libs.extend(libs)
	def add_bins(self, bins):
		""" Adds executable binaries to package from iterable. """
		if bins:
			self.bins.extend(bins)
	def add_docs(self, docs):
		""" Adds docs to package from iterable. """
		if docs:
			self.docs.extend(docs)
	def add_headers(self, headers):
		""" Adds include headers to package from iterable. """
		if headers:
			self.headers.extend(headers)
	def package_name(self):
		""" Returns package name.
		If there is no executables but only libraries, add prefix 'lib...'
		"""
		if self.libs and not self.bins:
			return 'lib' + self.name
		return self.name
	def full_name(self):
		""" Returns full package name (with version and arch). """
		full_package_name = '{name}_{version}_{arch}'.format(
				name=self.package_name(),
				version=self.version,
				arch=self.arch,
				)
		return full_package_name
	def filename(self):
		""" Returns result filename of the package. """
		return '{name}.deb'.format(name=self.full_name())
	def manifest(self):
		""" Returns content of the manifest file.
		Without trailing line break.
		"""
		lines = [
			'Package: {0}'.format(self.package_name()),
			'Version: {0}'.format(self.version),
			'Architecture: {0}'.format(self.arch),
			'Maintainer: {0}'.format(self.maintainer),
			'Description: {0}'.format(self.description or ''),
			]
		return '\n'.join(lines)

class AbstractBuilder(object):
	def __init__(self, build_dir=None, dest_dir=None):
		self.build_dir = Path(build_dir) if build_dir else None
		self.dest_dir = Path(dest_dir) if dest_dir else None
	def __enter__(self):
		return self
	def __exit__(self, *args, **kwargs):
		pass
	def remove_old_dir(self, path):
		raise NotImplementedError
	def install(self, src, dest, executable=True):
		raise NotImplementedError
	def symlink(self, src, dest):
		raise NotImplementedError
	def copy(self, src, dest):
		raise NotImplementedError
	def move(self, src, dest):
		raise NotImplementedError
	def write_file(self, filename, content):
		raise NotImplementedError
	def fakeroot(self, path):
		raise NotImplementedError

class DummyBuilder(AbstractBuilder):
	def __init__(self, build_dir=None, dest_dir=None):
		if build_dir is None:
			build_dir = '/tmp/dummy_dir'
		super(DummyBuilder, self).__init__(build_dir, dest_dir)
	def remove_old_dir(self, path):
		print('[DRY] Removing old build dir')
	def install(self, src, dest, executable=True):
		pass
	def symlink(self, src, dest):
		pass
	def copy(self, src, dest):
		pass
	def move(self, src, dest):
		print('[DRY] {0} -> {1}'.format(str(src), dest))
	def write_file(self, filename, content):
		print('[DRY] Writing file ({0}):'.format(filename))
		print(content)
	def fakeroot(self, path):
		print('[DRY] {0}'.format(['fakeroot', 'dpkg-deb', '--build', str(path)]))

class Builder(AbstractBuilder):
	def __init__(self, build_dir=None, dest_dir=None):
		self.remove_build_dir = None
		if build_dir is None:
			build_dir = tempfile.mkdtemp()
			self.remove_build_dir = build_dir
		super(Builder, self).__init__(build_dir, dest_dir)
	def __enter__(self):
		return self
	def __exit__(self, *args, **kwargs):
		if self.remove_build_dir:
			try:
				shutil.rmtree(str(self.remove_build_dir))
			except Exception as e:
				print(e)
	def remove_old_dir(self, path):
		shutil.rmtree(str(build_dir))
	def install(self, src, dest, executable=True):
		dest.parent.mkdir(parents=True, exist_ok=True)
		params = '-D'
		if not executable:
			params += 'm0644'
		subprocess.call(['install', '-D', str(stc), str(dest)])
	def symlink(self, src, dest):
		if not dest.exists():
			os.symlink(str(src), str(dest))
	def copy(self, src, dest):
		try:
			shutil.copy(str(src), str(dest))
		except IsADirectoryError:
			shutil.copytree(str(src), str(dest/Path(src).name))
	def move(self, src, dest):
		shutil.move(str(src), str(dest))
	def write_file(self, filename, content):
		filename.parent.mkdir(parents=True, exist_ok=True)
		filename.write_text(content + '\n')
	def fakeroot(self, path):
		subprocess.call(['fakeroot', 'dpkg-deb', '--build', str(path)])

@click.command()
@click.argument('package_name')
@click.option('-v', '--version', required=True, help='Package version.')
@click.option('--dry', is_flag=True, help='Dry run. Do not execute any actions, just log them.')
@click.option('--maintainer', default=os.environ['USER'], help='Maintaner of the package, usually in form "NAME <name@email>". By default current OS user is picked (name only).')
@click.option('--description', help='Package description (free text).')
@click.option('--bin', 'bins', multiple=True, help='Executables to install.')
@click.option('--lib', 'libs', multiple=True, help='Libraries to install.')
@click.option('--header', 'headers', multiple=True, help='Include headers to install.')
@click.option('--doc', 'docs', multiple=True, help='Docs to install.')
@click.option('--build-dir', help='Directory to store intermediate files. Default is within system temp directory.')
@click.option('--dest-dir', help='Directory to store final package. Default is one level up from build-dir.')
@click.option('--arch', help='Package architecture. Default is arch of the current system.')
def cli(package_name, version=None, dry=False, maintainer=None, description=None, bins=None, libs=None, headers=None, docs=None, build_dir=None, dest_dir=None, arch=None):
	""" Utility to create Debian package. """
	package = Package(package_name, version)
	package.add_libs(libs)
	package.add_bins(bins)
	package.add_docs(docs)
	package.add_headers(headers)
	package.set_maintainer(maintainer)
	package.set_description(description)

	BuilderType = Builder if not dry else DummyBuilder
	with BuilderType(build_dir, dest_dir) as builder:
		build_dir = builder.build_dir/package.full_name()
		if build_dir.exists():
			builder.remove_old_dir(build_dir)

		print('Creating build dir...')
		build_dir.mkdir(parents=True, exist_ok=True)

		for binfile in package.bins:
			dest = build_dir/'usr'/'local'/'bin'/Path(binfile).name
			print('Copying executable: {0}'.format(binfile))
			builder.install(binfile, dest)
		for lib in package.libs:
			dest = build_dir/'usr'/'local'/'lib'/Path(lib).name
			dest_version = Path(str(dest) + '.{0}'.format(package.version))
			print('Copying lib: {0}'.format(lib))
			builder.install(lib, dest_version)
			builder.symlink(dest_version.name, dest)
		for header in package.headers:
			dest = build_dir/'usr'/'local'/'include'/package.name
			dest_version = Path(str(dest) + '.{0}'.format(package.version))
			print('Copying header: {0}'.format(header))
			builder.install(header, dest_version/header, executable=False)
			builder.symlink(dest_version.name, dest)
		for doc in package.docs:
			dest = build_dir/'usr'/'local'/'share'/'doc'/package.name
			dest_version = Path(str(dest) + '.{0}'.format(package.version))
			dest_version.mkdir(parents=True, exist_ok=True)
			print('Copying docs: {0}'.format(doc))
			builder.copy(doc, dest_version)
			builder.symlink(dest_version.name, dest)

		print('Creating manifest...')
		debian_dir = build_dir/'DEBIAN'
		builder.write_file(debian_dir/'control', package.manifest())

		builder.fakeroot(build_dir)

		if builder.dest_dir:
			print('Moving package...')
			builder.move(build_dir/'..'/package.filename(), builder.dest_dir)
		print('Successfully done.')

if __name__ == '__main__':
	cli()
