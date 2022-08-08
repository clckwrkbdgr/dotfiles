import os
import datetime
import functools
import textwrap
try:
	textwrap.indent
except AttributeError: # pragma: no cover
	def indent(text, padding=' '):
		return ''.join(padding+line for line in text.splitlines(True))
	textwrap.indent = indent
import json
import functools
from .collections import AutoRegistry, dotdict
from . import xdg
from . import utils

providers = AutoRegistry()

@functools.total_ordering
class Entry:
	def __init__(self, date, title, details=None):
		self.date = date
		self.title = title
		self.details = details
	def __str__(self):
		result = '{0}: {1}'.format(self.date, self.title)
		if self.details:
			result += '\n' + textwrap.indent(self.details, '  ')
		return result
	def __repr__(self):
		return 'Entry(date={0}, title={1}, details=<{2} chars>)'.format(repr(self.date), repr(self.title), len(self.details or ''))
	def __lt__(self, other):
		if not isinstance(other, Entry):
			raise TypeError("Cannot compare Entry to {0}".format(type(other)))
		return (self.date, self.title, self.details) < (other.date, other.title, other.details)
	def __eq__(self, other):
		return (self.date, self.title, self.details) == (other.date, other.title, other.details)

def get_search_range(datestart=None, datestop=None, now=None):
	""" Parses given time period.

	Arguments should be specified in format: %Y%m%d%H%M%S
	If only one argument is specified, it should be just date: %Y%m%d
	If no arguments are given, whole current day is used.

	Returns datetime objects.
	"""
	now = now or datetime.datetime.now()
	if datestart is None:
		datestart = now
	else:
		try:
			datestart = datetime.datetime.strptime(datestart, '%Y%m%d%H%M%S')
		except:
			datestart = datetime.datetime.strptime(datestart, '%Y%m%d')
	if datestop is not None:
		datestop = datetime.datetime.strptime(datestop, '%Y%m%d%H%M%S')
	if datestop:
		return datestart, datestop
	return (datetime.datetime.combine(datestart.date(), datetime.time.min),
			datetime.datetime.combine(datestart.date(), datetime.time.max))

CONFIG_FILE_DESC = """Configuration is stored in $XDG_DATA_HOME/retro/config.json

\b
Fields:
- providers: list of entries:
	- module: name of the module with provider plugin;
	- provider_name: name of the provider function;
	- args: dict of arguments that should be passed to provider function.

Each provider function should accept at least two mandatory positional or keyword arguments: datestart, datestop.
Arguments specified in config file will be passed as additional keyword arguments to the function.
"""

@functools.lru_cache()
def read_config(): # pragma: no cover
	config_file = xdg.save_data_path('retro')/'config.json'
	data = {}
	if config_file.exists():
		data = json.loads(config_file.read_text())

	providers = []
	for provider_def in data.get('providers', []):
		provider_module, provider_function = utils.load_entry_point(os.path.expanduser(provider_def['module']) + ':' + provider_def['provider_name'])
		providers.append(dotdict(
			func=provider_function,
			args=provider_def.get('args', {}),
			))

	return dotdict(
			providers=providers
			)
