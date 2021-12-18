import subprocess
import itertools, functools
import re
from six.moves import shlex_quote
from clckwrkbdgr import xdg
from clckwrkbdgr.userservice import _base

SYSTEMD_UNIT_FILE = """\
[Unit]
Description={description}

[Service]
ExecStart=sh {user_env} {commandline}

[Install]
WantedBy=default.target
"""

class UserService(_base.UserService): # pragma: no cover -- TODO - subprocesses, FS
	@classmethod
	@functools.lru_cache()
	def _systemctl_show(cls, service_id):
		output = subprocess.check_output(['systemctl', '--user', 'show', str(service_id)]).decode('utf-8', 'replace')
		return dict(line.split('=', 1) for line in output.splitlines())
	def _get_wrapper_filename(self):
		return xdg.save_data_path('systemd')/'user'/(self.id+'.service')
	def _ensure_service_wrapper(self):
		wrapper_file = self._get_wrapper_filename()
		if wrapper_file.exists() and datetime.datetime.fromtimestamp(wrapper_file.stat().st_mtime) >= self.modification_time:
			return wrapper_file
		wrapper_file.parent.mkdir(parents=True, exist_ok=True)
		wrapper = SYSTEMD_UNIT_FILE .format(
				service_id = self.id,
				display_name = self.display_name or self.id,
				description = self.description,
				commandline = ' '.join(map(shlex_quote, self.commandline)),
				logfile = str(self.logfile),
				rootdir = str(self.rootdir),
				user_env = str(xdg.XDG_CONFIG_HOME/'bin'/'user-env.cmd'),
		)
		wrapper_file.write_text(wrapper)
		return wrapper_file

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
	def install(self):
		wrapper = self._ensure_service_wrapper()
		subprocess.check_call(['systemctl', '--user', 'daemon-reload'])
	def uninstall(self):
		self._get_wrapper_filename().unlink()
		subprocess.check_call(['systemctl', '--user', 'daemon-reload'])
	def start(self):
		subprocess.check_call(['systemctl', '--user', 'start', self.id])
	def stop(self):
		subprocess.check_call(['systemctl', '--user', 'stop', self.id])
