import os, sys, subprocess
import types, functools
try:
	types.SimpleNamespace
except AttributeError: # pragma: no cover
	import argparse
	types.SimpleNamespace = argparse.Namespace
import re, fnmatch
import inspect
import shlex
from collections import OrderedDict
import click
from clckwrkbdgr import utils
from clckwrkbdgr.click import RawEpilogGroup
from clckwrkbdgr.filterconf import Environment, ConfigFilter, config_filter

# ConfigFilters:
import clckwrkbdgr.filterconf.txt
import clckwrkbdgr.filterconf.jsonfile
import clckwrkbdgr.filterconf.firefox_prefs
import clckwrkbdgr.filterconf.inifile
import clckwrkbdgr.filterconf.sqlite

def get_epilog():
	result = 'FORMATS:\n'
	for name in config_filter.keys():
		filterclass = config_filter[name]
		result +=   '  {0}  - '.format(name)
		result += '\n         '.join(filterclass.description().splitlines())
		result += '\n'
	return result

def prepare_envvars(enviro_args):
	""" Registers requested environment variables and returns prepared Environment.
	Built-in variables: $HOME.
	"""
	envvars = Environment()
	envvars.register('HOME', lambda: os.getenv('HOME'))
	for enviro in enviro_args:
		if not '=' in enviro:
			raise Exception('Expected NAME=VALUE for -e argument, got {0}'.format(enviro))
		name, value = enviro.split('=', 1)
		if value.startswith('$'):
			varname = value[1:]
			if os.getenv(varname) is None:
				raise Exception('Environment variable {0} is not defined!'.format(varname))
			envvars.register(name, lambda varname=varname: os.getenv(varname))
		else:
			envvars.register(name, lambda command=value: subprocess.check_output(command, shell=True).decode('utf-8', 'replace').rstrip('\n'))
	return envvars

@click.group(cls=RawEpilogGroup, epilog=get_epilog())
@click.option('-f', '--format', required=True, type=click.Choice(list(config_filter.keys())),
		callback=lambda ctx, param, value: config_filter[value],
		help="Format of configuration file. "
		"See last section FORMATS for description of formats and actions. "
		"Supported formats: " + ', '.join(config_filter.keys()))
@click.option('-e', '--enviro', multiple=True, default=[],
		help="Custom variable for usage in filtering. "
		"Its value will be substitude with its name wherever found upon "
		"filtering, and will be substituted back with the value for the "
		"current system upon restoring. "
		"Should be in form NAME=VALUE, where value is either "
		"environment variable with dollar sign, e.g.: `HOME=$HOME`, "
		"or command which prints value to stdout, e.g.: `HOME=echo $HOME`. "
		"By default only $HOME is recognized.")
@click.pass_context
@utils.returns_exit_code
def main(ctx, format=None, enviro=None):
	""" Script to filter configuration files.
	Can process content with actions like sorting, replacing value,
	deleting value etc, see ACTIONS below.
	"""
	ctx.ensure_object(types.SimpleNamespace)
	ctx.obj.envvars = prepare_envvars(enviro)
	ctx.obj.format = format

def with_stdin_content(enviro_action=None):
	""" Reads stdin content and adds to context object under .content.
	After execution writes content back to stdout.
	If enviro_action = 'expand', expands environment variables in .envvars.
	Additionally, converts binary form to text representation.
	If enviro_action = 'restore', smudges environment variables in .envvars.
	Additionallly, converts text representation back to binary form.
	If incoming context object already has .content, all content actions are skipped.
	"""
	def _actual(func):
		@functools.wraps(func)
		def _wrapper(settings, *args, **kwargs):
			has_content = hasattr(settings, 'content')
			if not has_content:
				if enviro_action == 'expand':
					if sys.version_info >= (3, 0): # pragma: no cover -- os/py-version dependent.
						bin_stdin = sys.stdin.buffer
					else: # pragma: no cover -- os/py-version dependent.
						if sys.platform == "win32":
							import msvcrt
							msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
						bin_stdin = sys.stdin
					settings.content = settings.format.decode(bin_stdin.read()) # Expecting binary data.
					assert hasattr(settings.content, 'encode'), "Content decoded from stdin does not look like string."

					for name in settings.envvars.known_names():
						placeholder = '${0}'.format(name)
						settings.content = settings.content.replace(settings.envvars.get(name), placeholder)
				elif enviro_action == 'restore':
					settings.content = sys.stdin.read() # Expecting text.

					for name in settings.envvars.known_names():
						placeholder = '${0}'.format(name)
						if placeholder in settings.content:
							settings.content = settings.content.replace(placeholder, settings.envvars.get(name))
				elif enviro_action is not None: # pragma: no cover
					raise ValueError("enviro_action should be either None, 'expand' or 'restore'")
			try:
				return func(settings, *args, **kwargs)
			finally:
				if not has_content:
					if enviro_action == 'restore':
						if sys.version_info >= (3, 0): # pragma: no cover -- os/py-version dependent.
							bin_stdout = sys.stdout.buffer
						else: # pragma: no cover -- os/py-version dependent.
							if sys.platform == "win32":
								import msvcrt
								msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
							bin_stdout = sys.stdout
						data = settings.format.encode(settings.content)
						assert hasattr(data, 'decode'), "Encoded output does not look like binary data"
						bin_stdout.write(data) # Returning binary data.
					else:
						sys.stdout.write(settings.content) # Returning text representation.
					delattr(settings, 'content')
		return _wrapper
	return _actual

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='restore')
@utils.exits_with_return_value
def restore(settings):
	""" Restore filtered config file to normal state instead of filtering.
	That also includes converting back to original binary form, if format requires.
	"""
	pass

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def enviro(settings):
	""" Dummy action for the cases when only environment variables are needed to be expanded.
	Every other action will do the same expansion but "enviro" will do nothing except that
	and converting original binary form to text representation fit to be stored in VCS,
	if format requires.
	"""
	pass

@main.command()
@click.argument('path')
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def sort(settings, path):
	""" Sort content depending on format.
	See also `expand` command on additional implicit conversions.
	"""
	with settings.format(settings.content) as filter:
		filter.sort(path)
	settings.content = filter.content

@main.command()
@click.argument('path')
@click.argument('pattern')
@click.option('--pattern-type', default='plain', type=click.Choice('plain regex wildcard'.split()),
			help="Sets type of the supplied pattern (if any and if recognizable by current format)."
			)
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def delete(settings, path, pattern, pattern_type=None):
	""" Delete entries at provided path that match specified patterns (depends on format).
	See also `expand` command on additional implicit conversions.
	"""
	with settings.format(settings.content) as filter:
		filter.delete(path, pattern, pattern_type)
	settings.content = filter.content

@main.command()
@click.argument('path')
@click.argument('pattern')
@click.option('--pattern-type', default='plain', type=click.Choice('plain regex wildcard'.split()),
			help="Sets type of the supplied pattern (if any and if recognizable by current format)."
			)
@click.option('--with', 'with_value', nargs=1, required=True,
			help="Value to substitute. May contain references to the original value like refgroups for regexes (depends on format and pattern type)."
			)
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def replace(settings, path, pattern, pattern_type=None, with_value=None):
	""" Replace entry at specified path that match pattern with another value (depends on format).
	See also `expand` command on additional implicit conversions.
	"""
	with settings.format(settings.content) as filter:
		filter.replace(path, pattern, with_value, pattern_type)
	settings.content = filter.content

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def pretty(settings):
	""" Prettify content depending on format.
	See also `expand` command on additional implicit conversions.
	"""
	with settings.format(settings.content) as filter:
		filter.pretty()
	settings.content = filter.content

def parse_script_file(filename):
	""" Yields list of tuples: (command_name, [args])
	"""
	with open(filename) as f:
		for line in f:
			if not line.strip() or line.lstrip().startswith('#'):
				continue
			args = shlex.split(line)
			command_name = args.pop(0)
			yield command_name, args

@main.command()
@click.argument('filename')
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def script(settings, filename):
	""" Run several commands, stored in script file.
	Commands are applied in the given order.
	Format and enviro options do not need to be specified for each command,
	they are taken from main command line.
	See also `expand` command on additional implicit conversions,
	which will be performed once for all commands (before or after, depending on the conversion).
	"""
	with settings.format(settings.content) as filter:
		for command_name, args in parse_script_file(filename):
			try:
				try:
					command = globals()[command_name]
				except KeyError:
					raise ValueError('Unknown command: {0}. See usage for list of available commands.'.format(command))
				if not isinstance(command, click.core.Command):
					raise ValueError('Unknown command: {0}. See usage for list of available commands.'.format(command))
				rc = command(args=args, standalone_mode=False, obj=settings)
			except SystemExit as e:
				rc = e.code
			if rc != 0: # pragma: no cover
				return rc

if __name__ == '__main__': # pragma: no cover
	main()
