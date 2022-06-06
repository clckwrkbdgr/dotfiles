import bottle
from pathlib import Path
from clckwrkbdgr import xdg
from blackcompany import serve

ROOTDIR = Path(__file__).parent

serve.mime.Directory.List.serve('/docs', xdg.save_config_path('docs'), template_file=ROOTDIR/'template.html',
		title='Docs',
		content_template_file=ROOTDIR/'template_dirlist.html')
serve.mime.Text.Markdown.serve('/docs', xdg.save_config_path('docs'), path_param='filename', template_file=ROOTDIR/'template.html', encoding='utf-8')
serve.mime.Text.Markdown.serve('/docs/README.md', xdg.XDG_CONFIG_HOME/'README.md', template_file=ROOTDIR/'template.html')
serve.mime.Text.Plain.serve('/docs/LICENSE', xdg.XDG_CONFIG_HOME/'LICENSE')
