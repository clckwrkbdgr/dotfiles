#!/usr/bin/env python
import os, sys, subprocess
import configparser
from pathlib import Path
import functools, types
import contextlib
import logging
try:
	import termcolor
except ImportError:
	import clckwrkbdgr.dummy as termcolor
import clckwrkbdgr.fs

trace = logging.getLogger('setup')
class ColoredFormatter(logging.Formatter):
	COLORS = {
			'DEBUG': 'blue',
			'INFO': 'green',
			'WARNING': 'yellow',
			'CRITICAL': 'magenta',
			'ERROR': 'red',
			}
	def format(self, record):
		return termcolor.colored(
				super(ColoredFormatter, self).format(record),
				ColoredFormatter.COLORS.get(record.levelname, 'white'),
				)
_colored_stdout_handler = logging.StreamHandler()
_colored_stdout_handler.setFormatter(ColoredFormatter())
trace.addHandler(_colored_stdout_handler)

class Make(object):
	""" Decorator factory and repository for setup actions."""
	def __init__(self, rootdir=None):
		""" If rootdir is not specified, uses parent dir of this script. """
		self._rootdir = rootdir or Path(__file__).parent
		self._dry = False
		self._network = True
		self._actions = []
	def run(self, targets=None, dry=False, network=True):
		""" Runs registered actions according to the order of definition and corresponding conditions.
		Changes directory to the rootdir (see __init__).
		If network is False, does not execute network-dependent actions (see @needs_network).
		"""
		self._dry = dry
		self._network = network
		os.chdir(str(self._rootdir))
		if targets:
			actions = []
			for target in targets:
				matching = [action for action in make._actions if action.__name__ == target]
				if not matching:
					trace.error('No such action defined: {0}'.format(target))
					return False
				actions.extend(matching)
		else:
			actions = make._actions
		for action in actions:
			try:
				result = action()
			except Exception as e:
				trace.error(e, exc_info=True)
				result = False
			if not result:
				trace.warning('Stop.')
				return False
		trace.info('Done.')
		return True

	@property
	def with_context(self):
		""" Marks functions which needs target context to be passed to.
		Context should be passed as the first argument of the action function.
		Context is a namespace with following fields:
		- condition  - condition function object passed to target.
		- args  - condition's args (if there were any.
		- result  - actual result of the call of the condition function.
		"""
		def _decorator(func):
			func._needs_context = True
			return func
		return _decorator
	def with_name(self, name):
		""" Overrides name for condition.
		By default function's __name__ is used.
		"""
		def _decorator(func):
			func._condition_name = name
			return func
		return _decorator

	def when(self, condition, *condition_args):
		""" Decorator for function that tells Make to run the action function
		when condition is True.
		Condition should a callable that returns boolean value.
		If condition_args are supplied, they are passed to condition.
		Returns True upon success, False otherwise.
		Function is expected to return object that can be casted to bool,
		with the exception of None (e.g. when there is no return statement at all):
		in this case None is treated as True (i.e. Ok).
		If name is specified, it is used as name of the target,
		otherwise name of the condition function is used.
		"""
		def _decorator(func):
			@functools.wraps(func)
			def _wrapper(*args, **kwargs):
				condition_name = condition.__name__
				if hasattr(func, '_condition_name'):
					condition_name = func._condition_name
				condition_result = condition(*condition_args)
				if not condition_result:
					trace.info('Target {0} is up to date.'.format(condition_name))
					return True
				trace.warning('Target {0} is out of date.'.format(condition_name))
				if self._dry:
					trace.debug('Dry run, skipping action {0}'.format(func.__name__))
					return True
				trace.debug('Running action {0}'.format(func.__name__))
				try:
					if hasattr(func, '_needs_context') and func._needs_context:
						context = types.SimpleNamespace()
						context.condition = condition
						context.args = condition_args
						context.result = condition_result
						args = (context,) + args
					result = func(*args, **kwargs)
					if result is None:
						result = True
				except Exception as e:
					trace.error(e, exc_info=e)
					result = False
				if result:
					trace.info('Action {0} is successful.'.format(func.__name__))
				else:
					trace.error('Action {0} failed.'.format(func.__name__))
				return result
			self._actions.append(_wrapper)
			return _wrapper
		return _decorator
	def unless(self, condition, *args):
		""" Decorator for function that tells Make to run the action function
		unless condition is met.
		See description of when() for other details.
		"""
		return self.when(functools.wraps(condition)(lambda *_args, condition=condition: not condition(*_args)), *args)

	@property
	def needs_network(self): # TODO not used anymore, should be removed?
		""" Tells Make that action needs network to be executed.
		Otherwise it should be skipped.
		"""
		def _decorator(func):
			@functools.wraps(func)
			def _wrapper(*args, **kwargs):
				if not self._network:
					trace.warning('Switched off {0} because network is off.'.format(func.__name__))
					return None
				return func(*args, **kwargs)
			return _wrapper
		return _decorator

make = Make()

################################################################################

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Main setup script.')
	parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output. By default will print only errors and warnings.')
	parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true', default=False, help='Do not execute actions, just check conditions and report.')
	parser.add_argument('-N', '--no-network', dest='network', action='store_false', default=True, help='Skip targets that use network (e.g. on metered network connection or when there is no network at all).') # TODO isn't used anymore, should be removed?
	parser.add_argument('targets', nargs='*', help='Targets to make. By default makes all available targets one by one.')
	args = parser.parse_args()
	if args.verbose:
		trace.setLevel(logging.DEBUG)
	if not make.run(args.targets, dry=args.dry_run, network=args.network):
		sys.exit(1)
