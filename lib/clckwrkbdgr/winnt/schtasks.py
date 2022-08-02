import os, sys, subprocess
import tempfile
import logging
from collections import namedtuple
import xml.etree.ElementTree as ET
from clckwrkbdgr import xdg
from clckwrkbdgr import utils

TASK_XML_DEFINITION = """\
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
	<Triggers>
		<TimeTrigger>
			<!-- There is no option to register task to run by demand only, but it will not run tasks from very, very, very past. -->
			<StartBoundary>1901-01-01T00:00:00</StartBoundary>
			<Enabled>true</Enabled>
		</TimeTrigger>
	</Triggers>
	<Settings>
		<Priority>{priority}</Priority>
	</Settings>
	<Actions Context="Author">
		<Exec>
			<Command>{command}</Command>
			<Arguments>{command_args}</Arguments>
		</Exec>
	</Actions>
</Task>
"""

def run_immediately(commandline, task_scheduler_path, logdir=None, priority=7): # pragma: no cover -- calls external commands and available on Win only.
	""" Runs command (string) immediately using Windows Task Scheduler.
	Should produce not output.
	The job ID is generated in random manner.
	Job is stored in category specified by task_scheduler_path.

	Priority level 0 is the highest priority, and priority level 10 is the lowest priority.
	The default value is 7. Priority levels 7 and 8 are used for background tasks,
	and priority levels 4, 5, and 6 are used for interactive tasks.
	<https://docs.microsoft.com/en-us/windows/win32/taskschd/tasksettings-priority>

	Command is executed via clckwrkbdgr.commands facilities, i.e. output is captured and put in log file in specified log dir.
	See clckwrkbdgr.commands for details.
	"""
	try:
		assert 4 <= int(priority) <= 10
	except:
		raise RuntimeError("Expected integer priority in range [4; 10], got: {0}".format(priority))
	if utils.is_collection(commandline):
		commandline = subprocess.list2cmdline(commandline)
	command = ["pythonw", "-m", "clckwrkbdgr.commands"]
	command += ['--start-dir', subprocess.list2cmdline([os.getcwd()])]
	if logdir:
		command += ['--output-dir', subprocess.list2cmdline([str(logdir)])]
	command += [commandline]
	logging.debug('Running command: {0}'.format(command))
	command, command_args = command[0], ' '.join(command[1:])

	import time
	guid = str(time.time()).replace('.', '_') # TODO proper guid
	job_id = "{0}\\{1}".format(task_scheduler_path.rstrip('\\'), guid)
	logging.debug('Task Scheduler Job ID: {0}'.format(job_id))

	xml_content = TASK_XML_DEFINITION.format(
			command=command,
			command_args=command_args,
			priority=int(priority),
			).encode('cp1251', 'replace')
	try:
		task_xml = tempfile.NamedTemporaryFile(delete=False)
		task_xml.write(xml_content)
		task_xml.close()
		filename = task_xml.name
		try:
			output = subprocess.check_output(['schtasks', '/create', '/tn', job_id, '/xml', str(filename)], stderr=subprocess.STDOUT)
		except subprocess.CalledProcessError as e:
			sys.stderr.write(e.output.decode('ascii', 'replace'))
			raise
		logging.debug(output)
	finally:
		os.unlink(task_xml.name)
	output = subprocess.check_output(['schtasks', '/run', '/tn', job_id], stderr=subprocess.STDOUT)
	logging.debug(output)
	output = subprocess.check_output(['schtasks', '/delete', '/f', '/tn', job_id], stderr=subprocess.STDOUT)
	logging.debug(output)

class TaskScheduler: # pragma: no cover -- TODO calls external command and available on win only.
	RegistrationInfo = namedtuple('RegistrationInfo', 'author description uri')
	Task = namedtuple('Task', 'registration_info settings triggers actions')
	class Trigger:
		Repetition = namedtuple('Repetition', 'interval duration')
		ScheduleByDay = namedtuple('ScheduleByDay', 'days_interval')

		IdleTrigger = namedtuple('IdleTrigger', 'id enabled repetition')
		EventTrigger = namedtuple('EventTrigger', 'subscription delay execution_time_limit repetition')
		WnfStateChangeTrigger = namedtuple('WnfStateChangeTrigger', 'enabled delay state_name data')
		LogonTrigger = namedtuple('LogonTrigger', 'enabled delay repetition user_id start_boundary end_boundary')
		RegistrationTrigger = namedtuple('RegistrationTrigger', 'delay')
		BootTrigger = namedtuple('BootTrigger', 'enabled delay repetition')
		TimeTrigger = namedtuple('TimeTrigger', 'enabled start_boundary random_delay repetition')
		SessionStateChangeTrigger = namedtuple('SessionStateChangeTrigger', 'enabled state_change user_id')
		CalendarTrigger = namedtuple('CalendarTrigger', 'enabled start_boundary end_boundary random_delay schedule_by_day execution_time_limit repetition')
	class Action:
		Exec = namedtuple('ActionExec', 'command arguments working_directory')
		ComHandler = namedtuple('ComHandler', 'class_id data')

	def __init__(self):
		self.nsmap = {
				'tasks' : 'http://schemas.microsoft.com/windows/2004/02/mit/task',
				}
	def get_child_text(self, element, child_name):
		child = element.find('./tasks:{0}'.format(child_name), namespaces=self.nsmap)
		if child is None:
			return None
		return child.text
	def get_tag_name(self, element):
		return element.tag.split('}')[-1]
	def create_object_from_node(self, class_root, node):
		object_class = getattr(class_root, self.get_tag_name(node))
		fields = [''.join(map(str.title, field.split('_'))) for field in object_class._fields]
		for subelement in node.find('.', namespaces=self.nsmap):
			if self.get_tag_name(subelement) not in fields:
				logging.warning("Unknown field for node {1}: {0}".format(ET.tostring(subelement), self.get_tag_name(node)))
		values = []
		for field in fields:
			if field in class_root.__dict__:
				child = node.find('./tasks:{0}'.format(field), namespaces=self.nsmap)
				if child is not None:
					values.append(self.create_object_from_node(class_root, child))
				else:
					values.append(None)
			else:
				values.append(self.get_child_text(node, field))
		return object_class(*values)

	def iter_all(self):
		try:
			command = ['schtasks', '/query', '/XML', 'ONE']
			output = subprocess.check_output(command)
		except Exception as e:
			logging.error("Failed to collect schtasks dump {0}: {1}\n".format(command, e))
			return
		dom = ET.ElementTree(ET.fromstring(output))
		for task in dom.findall('./tasks:Task', namespaces=self.nsmap):
			registration_info = task.find('./tasks:RegistrationInfo', namespaces=self.nsmap)
			registration_info = self.RegistrationInfo(
					self.get_child_text(registration_info, 'Author'),
					self.get_child_text(registration_info, 'Description'),
					self.get_child_text(registration_info, 'URI'),
					)

			settings = {}
			for setting in task.findall('./tasks:Settings/', namespaces=self.nsmap):
				if self.get_tag_name(setting) == 'IdleSettings':
					for subsetting in setting.findall('./tasks:IdleSettings/', namespaces=self.nsmap):
						subname = subsetting.tag.split('}')[-1]
						subvalue = subsetting.text
						settings[subname] = subvalue
				else:
					value = setting.text
					settings[self.get_tag_name(setting)] = value

			triggers = []
			for trigger in task.find('./tasks:Triggers', namespaces=self.nsmap):
				if self.get_tag_name(trigger) in self.Trigger.__dict__:
					triggers.append(self.create_object_from_node(
						self.Trigger, trigger,
						))
				else:
					logging.warning('Unknown trigger class: {0}'.format(ET.tostring(trigger)))

			actions = []
			for action in task.find('./tasks:Actions', namespaces=self.nsmap):
				if self.get_tag_name(action) in self.Action.__dict__:
					actions.append(self.create_object_from_node(
						self.Action, action,
						))
				else:
					logging.warning('Unknown action class: {0}'.format(ET.tostring(action)))

			yield self.Task(registration_info, settings, triggers, actions)
