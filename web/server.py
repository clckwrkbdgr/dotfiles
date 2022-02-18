import blackcompany.concurrent
import blackcompany
import blackcompany.serve
import os

badger_web_root = os.environ.get('BADGER_WEB_ROOT')
if badger_web_root and os.path.isdir(badger_web_root):
	blackcompany.serve.plugin.discover(badger_web_root)

if __name__ == '__main__':
	blackcompany.run_cli(host='0.0.0.0', port=20113) # 20113 == ZONE
