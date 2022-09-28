import json
import bottle
from pathlib import Path
from clckwrkbdgr import xdg

ROOTDIR = Path(__file__).resolve().parent
DOTFILES_ROOTDIR = ROOTDIR.parent.parent

@bottle.route('/lib/<javascript_module>.js')
def host_dotfiles_js_library(javascript_module):
	bottle.response.content_type = 'application/javascript'
	return (DOTFILES_ROOTDIR/'lib'/'{0}.js'.format(javascript_module)).read_text()

@bottle.post('/lib/save_to_fs_storage')
def save_to_fs_storage():
	data = bottle.request.body.read().decode('utf-8', 'replace')
	data = json.loads(data)
	domain = data['domain']
	name = data['name']
	value = data['value']

	local_path = xdg.save_state_path('firefox')/'localstorage'
	local_path.mkdir(parents=True, exist_ok=True)

	filename = local_path/'{0}.json'.format(domain)
	data = {}
	if filename.exists():
		data = json.loads(filename.read_text())
	data[name] = value
	filename.write_text(json.dumps(data))

@bottle.route('/lib/test/test_<javascript_module>.html')
def host_dotfiles_js_library(javascript_module):
	return (DOTFILES_ROOTDIR/'lib'/'test'/'test_{0}.html'.format(javascript_module)).read_text()

@bottle.post('/lib/test/test_<javascript_module>.html')
def post_test_results(javascript_module):
	pass

@bottle.route('/lib/test/userscript')
@bottle.route('/lib/test/userscript_with_grant')
def test_userscripts():
	return (DOTFILES_ROOTDIR/'web'/'dotfiles'/'test_userscript.html').read_text()

@bottle.post('/lib/test/save_to_fs_storage')
def test_save_to_fs_storage():
	data = bottle.request.body.read().decode('utf-8', 'replace')
	data = json.loads(data)
	print(data)
