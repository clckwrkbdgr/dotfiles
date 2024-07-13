# Sometimes Firefox just resets addons.json (clearing all data) while running.
# As there is no other place of truth, picking the last available revision to prevent git from detecting "changes".
import sys, json
content = sys.stdin.read()
data = json.loads(content)
if not data['addons']:
	import subprocess
	content = subprocess.check_output(['git', 'show', 'HEAD:firefox/addons.json']).decode('utf-8', 'replace')
sys.stdout.write(content)
