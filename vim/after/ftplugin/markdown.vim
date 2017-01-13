" Folds Markdown text by headings, apparently to any level of nesting.
" Taken from:
"   http://stackoverflow.com/a/4677454/2128769
" With additional changes from:
"   http://stackoverflow.com/questions/3828606/vim-markdown-folding#comment16309004_4677454

function! MarkdownLevel()
	let h = matchstr(getline(v:lnum), '^#\+')
	if empty(h)
		return "="
	else
		return ">" . len(h)
	endif
endfunction

au BufEnter *.md setlocal foldexpr=MarkdownLevel()  
au BufEnter *.md setlocal foldmethod=expr  
