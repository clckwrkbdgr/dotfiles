import blackcompany.concurrent
import blackcompany
import blackcompany.serve
import os, sys

badger_web_root = os.environ.get('BADGER_WEB_ROOT')
if badger_web_root and os.path.isdir(badger_web_root):
	blackcompany.serve.plugin.discover(badger_web_root)
blackcompany.serve.plugin.discover(os.path.join(os.path.dirname(__file__), 'dotfiles'))

if __name__ == '__main__':
	if sys.argv[1:] == ['test']:
		del sys.argv[1]
		blackcompany.run_cli(host='127.0.0.1', port=2113) # 2113 == ZNE
	else:
		blackcompany.run_cli(host='0.0.0.0', port=20113) # 20113 == ZONE
