import os, sys, subprocess
import datetime
import six
from clckwrkbdgr import xdg
from clckwrkbdgr.userservice import _base

WRAPPER = """\
import os, sys, subprocess, time
import win32serviceutil, win32event, win32service, servicemanager
class CustomWindowsService(win32serviceutil.ServiceFramework):
	_svc_name_ = {service_id}
	_svc_display_name_ = {display_name}
	_svc_description_ = {description}
	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
	@classmethod
	def cli(cls):
		win32serviceutil.HandleCommandLine(cls)
	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)
	def SvcDoRun(self):
		self.ReportServiceStatus(win32service.SERVICE_RUNNING)
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
				servicemanager.PYS_SERVICE_STARTED,
				(self._svc_name_,''))
		try:
			self.main()
		except Exception as e:
			import traceback
			servicemanager.LogErrorMsg(str(traceback.format_exc()))
	def main(self):
		self.command = {commandline}
		self.logfile = {logfile}
		self.rootdir = {rootdir}
		if self.rootdir and os.path.isdir(str(self.rootdir)):
			os.chdir(str(self.rootdir))
		logdir = os.path.dirname(str(self.logfile))
		if not os.path.isdir(logdir):
			os.makedirs(logdir)
		with open(str(self.logfile), 'ab+') as flog:
			p = subprocess.Popen(self.command, stdin=subprocess.DEVNULL, stdout=flog, stderr=subprocess.STDOUT)
			win32event.WaitForMultipleObjects([self.hWaitStop], False, win32event.INFINITE)
			p.terminate()
			rc = p.wait()
			flog.write(('[Terminated with RC='+str(rc)+']\\n').encode('utf-8', 'replace'))
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
				servicemanager.PYS_SERVICE_STOPPED,
				(self._svc_name_,''))
if __name__ == "__main__":
	CustomWindowsService.cli()
"""

class UserService(_base.UserService): # pragma: no cover -- TODO - subprocesses, FS
	def _ensure_service_wrapper(self):
		wrapper_file = xdg.save_cache_path('userservice')/'windows'/(self.id+'.py')
		if wrapper_file.exists() and datetime.datetime.fromtimestamp(wrapper_file.stat().st_mtime) >= self.modification_time:
			return wrapper_file
		wrapper_file.parent.mkdir(parents=True, exist_ok=True)
		wrapper = WRAPPER.format(
				service_id = repr(self.id),
				display_name = repr(self.display_name or self.id),
				description = repr(self.description),
				commandline = repr(self.commandline),
				logfile = repr(self.logfile),
				rootdir = repr(self.rootdir),
		)
		wrapper_file.write_text(wrapper)
		return wrapper_file
	def is_installed(self):
		rc = subprocess.call(["sc", "query", self.id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		return 0 == rc
	def install(self):
		wrapper = self._ensure_service_wrapper()
		domain = os.environ['USERDOMAIN']
		username = os.environ['USERNAME']
		qualified_username = '{0}\\{1}'.format(domain, username)
		import getpass
		password = getpass.getpass('Enter password for {0}: '.format(qualified_username))
		subprocess.check_call(['python', str(wrapper),
			'--username', qualified_username,
			'--password', password,
			'install',
			])
	def uninstall(self):
		wrapper = self._ensure_service_wrapper()
		subprocess.check_call(['python', str(wrapper), 'remove'])
	def is_started(self):
		try:
			output = subprocess.check_output(["sc", "query", self.id], stderr=subprocess.DEVNULL)
			for line in output.splitlines():
				if b'STATE' in line and not b'STOPPED' in line:
					return True
		except:
			pass
		return False
	def start(self):
		wrapper = self._ensure_service_wrapper()
		subprocess.check_call(['python', str(wrapper), 'start'])
	def stop(self):
		wrapper = self._ensure_service_wrapper()
		subprocess.check_call(['python', str(wrapper), 'stop'])
