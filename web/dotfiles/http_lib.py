import bottle
from pathlib import Path
from clckwrkbdgr import xdg

ROOTDIR = Path(__file__).parent

@bottle.route('/lib/<javascript_module>.js')
def host_dotfiles_js_library(javascript_module):
	bottle.response.content_type = 'application/javascript'
	return (xdg.save_config_path('lib')/'{0}.js'.format(javascript_module)).read_text()

@bottle.route('/lib/test/test_<javascript_module>.html')
def host_dotfiles_js_library(javascript_module):
	return (xdg.save_config_path('lib')/'test'/'test_{0}.html'.format(javascript_module)).read_text()

@bottle.route('/lib/test/userscript')
@bottle.route('/lib/test/userscript_with_grant')
def test_userscripts():
	return (ROOTDIR/'test_userscript.html').read_text()
