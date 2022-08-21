import bottle
from pathlib import Path
from clckwrkbdgr import xdg

ROOTDIR = Path(__file__).resolve().parent
DOTFILES_ROOTDIR = ROOTDIR.parent.parent

@bottle.route('/lib/<javascript_module>.js')
def host_dotfiles_js_library(javascript_module):
	bottle.response.content_type = 'application/javascript'
	return (DOTFILES_ROOTDIR/'lib'/'{0}.js'.format(javascript_module)).read_text()

@bottle.route('/lib/test/test_<javascript_module>.html')
def host_dotfiles_js_library(javascript_module):
	return (DOTFILES_ROOTDIR/'lib'/'test'/'test_{0}.html'.format(javascript_module)).read_text()

@bottle.route('/lib/test/userscript')
@bottle.route('/lib/test/userscript_with_grant')
def test_userscripts():
	return (DOTFILES_ROOTDIR/'test_userscript.html').read_text()
