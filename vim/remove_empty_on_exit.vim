fun! s:RemoveFileIfEmpty(fname)
	if getfsize(a:fname) == 0
		call delete(a:fname)
	endif
endfun

augroup autocom
	autocmd!
	autocmd VimLeave * call s:RemoveFileIfEmpty(expand('%:p'))
augroup END
