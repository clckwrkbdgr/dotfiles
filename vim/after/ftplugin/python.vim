set autoindent

" Return 1 if using tabs for indents, or 0 otherwise.
function PyIsTabIndent()
  let lnum = 1
  let got_cols = 0  " 1 if previous lines ended with columns
  while lnum <= 100
    let line = getline(lnum)
    let lnum = lnum + 1
    if got_cols == 1
      if line =~ "^\t\t"  " two tabs to prevent false positives
        return 1
      endif
    endif
    if line =~ ":\s*$"
      let got_cols = 1
    else
      let got_cols = 0
    endif
  endwhile
  return 0
endfunction

" Check current buffer and configure for tab or space indents.
function PyIndentAutoCfg()
  if PyIsTabIndent()
    set noexpandtab
  else
    set expandtab
  endif
endfunction
