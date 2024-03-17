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

"""
xml:
	delete tag (full node) by xpath
	delete
	replace attribute value by xpath
	sort ?
	sort-xml - sort tags by attribute

firefox pref.js
	user_pref("accessibility.blockautorefresh", true);
	delete preference by pattern (including regexp and wildcard)
	replace preference value by name and possibly regexp pattern with match groups

ini:
	sort sections/ sort values in sections
	delete ini setting by section/name
	delete whole section
	including search by regexp
	replace value for given section/name to another one
	including regexp and regexp match groups

scheme:
	delete value by setting name (including regex in names)
	"""

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
	If enviro_action = 'restore', smudges environment variables in .envvars.
	If incoming context object already has .content, all content actions are skipped.
	"""
	def _actual(func):
		@functools.wraps(func)
		def _wrapper(settings, *args, **kwargs):
			has_content = hasattr(settings, 'content')
			if not has_content:
				settings.content = sys.stdin.read()
				if enviro_action == 'expand':
					for name in settings.envvars.known_names():
						placeholder = '${0}'.format(name)
						settings.content = settings.content.replace(settings.envvars.get(name), placeholder)
				elif enviro_action == 'restore':
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
					sys.stdout.write(settings.content)
					delattr(settings, 'content')
		return _wrapper
	return _actual

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='restore')
@utils.exits_with_return_value
def restore(settings):
	""" Restore filtered config file to normal state instead of filtering. """
	pass

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def enviro(settings):
	""" Dummy action for the cases when only environment variables are needed to be expanded.
	Every other action will do the same expansion but "enviro" will do nothing except that.
	"""
	pass

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def sort(settings):
	""" Sort content depending on format. """
	filter = settings.format(settings.content)
	filter.sort()
	settings.content = filter.content

@main.command()
@click.argument('patterns', nargs=-1)
@click.option('--pattern-type', default='plain', type=click.Choice('plain regex wildcard'.split()),
			help="Sets type of the supplied pattern (if any and if recognizable by current format)."
			)
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def delete(settings, patterns, pattern_type=None):
	""" Delete entries that match specified patterns/paths (depends on format). """
	filter = settings.format(settings.content)
	for pattern in patterns:
		filter.delete(pattern, pattern_type)
	settings.content = filter.content

@main.command()
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
def replace(settings, pattern, pattern_type=None, with_value=None):
	""" Replace entry specified by pattern/path with another value (depends on format). """
	filter = settings.format(settings.content)
	filter.replace(pattern, with_value, pattern_type)
	settings.content = filter.content

@main.command()
@click.pass_obj
@with_stdin_content(enviro_action='expand')
@utils.exits_with_return_value
def pretty(settings):
	""" Prettify content depending on format. """
	filter = settings.format(settings.content)
	filter.pretty()
	settings.content = filter.content

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
	"""
	with open(filename) as f:
		for line in f:
			if not line.strip() or line.lstrip().startswith('#'):
				continue
			try:
				args = shlex.split(line)
				command_name = args.pop(0)
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
