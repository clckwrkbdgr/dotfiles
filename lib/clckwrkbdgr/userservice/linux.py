import subprocess
import itertools, functools
import re
from clckwrkbdgr.userservice import _base

class UserService(_base.UserService): # pragma: no cover -- TODO - subprocesses, FS
	@classmethod
	@functools.lru_cache()
	def _systemctl_show(cls, service_id):
		output = subprocess.check_output(['systemctl', '--user', 'show', str(service_id)]).decode('utf-8', 'replace')
		return dict(line.split('=', 1) for line in output.splitlines())
	@classmethod
	def list_all(cls):
		# systemctl have no formatting except 'fancy' because Poettering "try to keep things minimal there"
		# https://github.com/systemd/systemd/issues/83
		output = subprocess.check_output(['systemctl', '--user', 'list-units', '--type=service', '--all'])
		header = []
		header_values = []
		for line in output.decode('utf-8', 'replace').splitlines():
			if not header:
				header = [_ for _ in re.split(r'(\b\w+\s+)', line) if _]
				header_values = [_.strip() for _ in header]
				continue
			if not line:
				break
			columns = list(itertools.accumulate(map(len, header)))
			row = [line[start:stop].strip() for (start, stop) in zip([0] + columns, columns)]
			values = dict(zip(header_values, row))
			if values['UNIT'].endswith('.service'):
				values['UNIT'] = values['UNIT'][:-len('.service')]
			yield cls.Status(values['UNIT'], values['SUB'] == 'running')
	def is_installed(self):
		status = self._systemctl_show(self.id)
		return status['LoadState'] == 'loaded'
	def is_started(self):
		status = self._systemctl_show(self.id)
		return status['SubState'] == 'running'
