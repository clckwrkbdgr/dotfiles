" Folds Markdown text by headings, apparently to any level of nesting.
" Taken from:
"   http://stackoverflow.com/a/4677454/2128769
" With additional changes from:
"   http://stackoverflow.com/questions/3828606/vim-markdown-folding#comment16309004_4677454
" Updated with code shamelessly ripped from tpope/vim-markdown:
"   https://github.com/tpope/vim-markdown/blob/master/ftplugin/markdown.vim

function! MarkdownLevel()
	let line = getline(v:lnum)

	if line =~# '^#\+ '
		return ">" . match(line, ' ')
	endif

	let nextline = getline(v:lnum + 1)
	if (line =~ '^.\+$') && (nextline =~ '^=\+$')
		return ">1"
	endif

	if (line =~ '^.\+$') && (nextline =~ '^-\+$')
		return ">2"
	endif

	return "="
endfunction

au BufEnter *.md setlocal foldexpr=MarkdownLevel()  
au BufEnter *.md setlocal foldmethod=expr  
