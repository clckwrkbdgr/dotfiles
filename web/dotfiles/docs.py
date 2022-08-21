import bottle
from pathlib import Path
from clckwrkbdgr import xdg
from blackcompany import serve

ROOTDIR = Path(__file__).resolve().parent
DOTFILES_ROOTDIR = ROOTDIR.parent.parent

serve.mime.Directory.List.serve('/docs', DOTFILES_ROOTDIR/'docs', template_file=ROOTDIR/'template.html',
		title='Docs',
		content_template_file=ROOTDIR/'template_dirlist.html')
serve.mime.Text.Markdown.serve('/docs', DOTFILES_ROOTDIR/'docs', path_param='filename', template_file=ROOTDIR/'template.html', encoding='utf-8')
serve.mime.Text.Markdown.serve('/docs/README.md', DOTFILES_ROOTDIR/'README.md', template_file=ROOTDIR/'template.html')
serve.mime.Text.Plain.serve('/docs/LIC' + 'ENSE', DOTFILES_ROOTDIR/('LIC' + 'ENSE')) # Keyword is split so corresponding search would not be triggered.
