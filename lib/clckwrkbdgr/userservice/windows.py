from __future__ import print_function
import os, sys, subprocess
import re
import datetime, time
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
	@classmethod
	def _get_profile_sid(cls, userprofile_path):
		import clckwrkbdgr.winnt.registry
		import winreg
		profile_list = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'
		for sid in clckwrkbdgr.winnt.registry.iterkeys(winreg.HKEY_LOCAL_MACHINE, profile_list):
			for name, value, value_type in clckwrkbdgr.winnt.registry.itervalues(winreg.HKEY_LOCAL_MACHINE, profile_list + '\\' + sid):
				if name == 'ProfileImagePath' and value == userprofile_path:
					return sid
	@classmethod
	def _grant_control_rights(cls, service_id, userprofile_path):
		""" It may fail for some reason to give proper rights despite saying SUCCESS.
		In this case go to gpedit.msc -> Computer Configuration/Windows Settings/Security Settings/System Services.
		If this category is not available:
		- Run 'mmc', "File->Add/Remove Snap In...", add "Security Templates" and save console to somewhere (default location is ok).
		- Locate and open newly created console, switch to "Security Templates" and create new template, it should contain System Services.
		Select your service, from context menu to to Properties/Edit Security.
		Add your account and set Start/Stop permisions.
		NOTE: It may still not work for unknown reasons, like some domain policies may override local settings.
		"""
		sid = cls._get_profile_sid(userprofile_path)
		if not sid:
			raise RuntimeError("Cannot find Windows Profile SID for current user ({0})".format(userprofile_path))
		sdshow = subprocess.check_output(['sc', 'sdshow', service_id]).decode().strip()
		SDSHOW = re.compile(r'^(D:)(\([^()]+\))(.*)(S:)(\(AU;[^()]+\))(.*)$')
		parts = SDSHOW.match(sdshow)
		if not parts:
			raise RuntimeError("Failed to find S:(AU;...) part in 'sc sdhow ...', looks like command is not executed in elevated privileges.")
		parts = list(parts.groups())
		assert ''.join(parts) == sdshow
		parts.insert(-3, '(A;;CCLCSWRPWPDTLOCRRC;;;{0})'.format(sid))
		adjusted_sdshow = ''.join(parts)
		subprocess.check_call(['sc', '\\\\localhost', 'sdset', service_id, adjusted_sdshow])

	@classmethod
	def list_all(cls):
		domain = os.environ['USERDOMAIN']
		username = os.environ['USERNAME']
		qualified_username = '{0}\\{1}'.format(domain, username)
		fqdn = next(line for line in subprocess.check_output(['ipconfig', '/all']).decode().splitlines() if line.lstrip().startswith('Primary Dns Suffix')).split(':')[-1].strip()
		fully_qualified_username = '{1}@{0}'.format(fqdn, username)

		output = subprocess.check_output([
			'wmic', 'service',
			'where', 'StartName like "{0}" OR StartName like "{1}"'.format(qualified_username.replace('\\', '\\\\'), fully_qualified_username),
			'get', '/format:csv',
			], shell=True)
		import csv
		for row in csv.DictReader(filter(None, output.decode('utf-8', 'replace').splitlines())):
			yield cls.Status(row['Name'], row['State'] == 'Running')
	def is_installed(self):
		rc = subprocess.call(["sc", "query", self.id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		return 0 == rc
	def install(self):
		wrapper = self._ensure_service_wrapper()
		username = os.environ['USERNAME']
		# Windows 11 may require fully-quialified domain name.
		# Otherwise it may fail to start the first time because user may have no rights to "Logon as a service"
		# So it has to be granted manually first:
		# <https://stackoverflow.com/questions/25619112/how-do-i-fix-the-error1069-the-service-did-not-start-due-to-logon-failure>
		fqdn = next(line for line in subprocess.check_output(['ipconfig', '/all']).decode().splitlines() if line.lstrip().startswith('Primary Dns Suffix')).split(':')[-1].strip()
		fully_qualified_username = '{1}@{0}'.format(fqdn, username)
		import getpass
		password = getpass.getpass('Enter password for {0}: '.format(fully_qualified_username))
		subprocess.check_call(['python', str(wrapper),
			'--username', fully_qualified_username,
			'--password', password,
			'--startup=delayed',
			'install',
			])
		self._grant_control_rights(self.id, os.environ['USERPROFILE'])
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
		try:
			subprocess.check_call(['sc', 'start', self.id])
		except subprocess.CalledProcessError as e:
			if e.returncode == 1053: # Error starting service: The service did not respond to the start or control request in a timely fashion.
				self._check_pywin32_libs()
			elif e.returncode == 1056: # An instance of the service is already running.
				# If start is called immediately after stop (during restart),
				# services might not be stopped yet.
				time.sleep(1) # We will sleep a fair amount of time,
				return subprocess.check_call(['sc', 'start', self.id]) # And just retry, and then fail for real.
			raise
	def _check_pywin32_libs(self):
		import win32api
		package_dir = os.path.dirname(win32api.__file__)
		pywintypes_dll = 'pywintypes{0}{1}.dll'.format(*(sys.version_info[:2]))
		expected_dll = os.path.join(package_dir, pywintypes_dll)
		if not os.path.isfile(expected_dll):
			print('Possible reason: Missing library in pywin32 module directory:\n  {0}'.format(expected_dll), file=sys.stderr)
			possible_location = os.path.join(os.path.dirname(package_dir), 'pywin32_system32', pywintypes_dll)
			if os.path.isfile(possible_location):
				print('Found this lib in different location:\n  {0}\nTry to copy it to {1} and re-check'.format(possible_location, expected_dll), file=sys.stderr)
	def stop(self):
		wrapper = self._ensure_service_wrapper()
		subprocess.check_call(['sc', 'stop', self.id])
		for wait_to_stop_seconds in range(10):
			if not self.is_started():
				return True
