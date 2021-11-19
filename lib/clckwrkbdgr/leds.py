import subprocess
try:
	from PIL import Image
except: # pragma: no cover
	Image = None
from clckwrkbdgr import xdg

def join_image_strip(image_files, output_file): # pragma: no cover -- TODO images
	""" Join multiple image files into a single horizontal strip. """
	if not image_files:
		empty_transparent_pixel = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
		empty_transparent_pixel.save(str(output_file))
		return
	frames = [Image.open(str(image)) for image in image_files if image]
	widths = [image.width for image in frames]
	full_width, frame_width = sum(widths), max(widths)
	full_height = max([image.width for image in frames])
	band = Image.new('RGBA', (full_width, full_height))
	for index, frame in enumerate(frames):
		band.paste(frame, (frame_width * index, 0))
	band.save(str(output_file))

class GenMon: # pragma: no cover -- TODO OS
	IMAGE_PATH = xdg.save_runtime_path('xfce4', 'leds')/"state.png"
	TOOLTIP_PATH = xdg.save_runtime_path('xfce4', 'leds')/"state.txt"

	def __init__(self, genmon_id):
		self.genmon_id = genmon_id
	def update(self, plugins):
		tooltip = []
		images = []
		for group in plugins:
			tooltip.append(group.title)
			images.append(group.image)
		tooltip = '\n'.join(tooltip)
		try:
			join_image_strip(images, GenMon.IMAGE_PATH)
		except:
			import traceback
			traceback.print_exc()
		GenMon.TOOLTIP_PATH.write_text(tooltip)
	def refresh_plugin(self):
		# FIXME works only with xfce4-plugin-genmon >= 4.0.2, but there is no way to get current version of a plugin.
		# FIXME otherwise need to set genmon to refresh rate = 1s
		subprocess.call(['xfce4-panel', '--plugin-event={0}:refresh:bool:true'.format(self.genmon_id)])

	@staticmethod
	def get_text():
		GenMon.IMAGE_PATH = xdg.save_runtime_path('xfce4', 'leds')/"state.png"
		GenMon.TOOLTIP_PATH = xdg.save_runtime_path('xfce4', 'leds')/"state.txt"
		return "<img>{0}</img>\n<tool>{1}</tool>\n".format(GenMon.IMAGE_PATH, GenMon.TOOLTIP_PATH.read_text())

class LEDList: # pragma: no cover - TODO threads
	def __init__(self):
		self.items = []
		self.changed = threading.Event()
		self.lock = threading.Lock()
	def set(self, item):
		with self.lock:
			if item not in self.items:
				self.items.append(item)
			self.changed.set()
	def unset(self, item):
		with self.lock:
			try:
				self.items.remove(item)
				self.changed.set()
			except ValueError:
				pass
	def get(self):
		return self.items
	def callback(self, plugin, state):
		if state:
			self.set(plugin)
		else:
			self.unset(plugin)
