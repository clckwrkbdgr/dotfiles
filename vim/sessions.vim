""" Sessions
function! MkSession(...)
	if empty(a:000) " TODO current does not read any other file than default .session.vim; see TryToRestoreSession
		let filename = ".session.vim"
	else
		let filename = fnameescape(a:1)
	endif

	" Collecting custom status.
	"let need_nerdtree = g:NERDTree.IsOpen()
	tabdo NERDTreeClose " So its raw window content won't get into session.

	" Base mksession.
	execute 'mksession! ' . filename

	" Adding custom status.
	"if need_nerdtree
		"TODO : rewriting session file corrupts key mapping with <CR> because
		"it is stored as ^M, which on consequent write disappears and messes
		"up next lines.
		"call writefile(readfile(filename) + ['NERDTree', 'exec "normal \<C-W>\<C-w>"'], filename)
		"NERDTree " Restore NERDTree window if needed.
	"endif
endfunction

let g:dotsession_file_was_found = 0 " FIXME Actually should store session file name.

function! AutoMakeSession()
	if g:dotsession_file_was_found != 0
		call MkSession()
	endif
endfunction

function! TryToRestoreSession()
	if len(argv()) == 0 && filereadable(getcwd() . '/.session.vim')
		execute 'so ' . getcwd() . '/.session.vim'
		let g:dotsession_file_was_found = 1
		if bufexists(1)
			for l in range(1, bufnr('$'))
				if bufwinnr(l) == -1
					exec 'sbuffer ' . l
				endif
			endfor
		endif
	endif
endfunction

command! -nargs=? MKS call MkSession(<f-args>)
autocmd VimEnter * nested call TryToRestoreSession()
autocmd VimLeave * :call AutoMakeSession()

