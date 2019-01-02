" Return 1 if using tabs for indents, or 0 otherwise.
function ftplugin#python#PyIsTabIndent()
  let lnum = 1
  let got_cols = 0  " 1 if previous lines ended with columns
  let has_space_indents = 0
  while lnum <= 100
    let line = getline(lnum)
    let lnum = lnum + 1
    if got_cols == 1
      if line =~ "^\t\t"  " two tabs to prevent false positives
        return 1
      endif
      if line =~ "^    "  " four spaces to prevent false positives
        let has_space_indents = 1
      endif
    endif
    if line =~ ":\s*$"
      let got_cols = 1
    else
      let got_cols = 0
    endif
  endwhile
  if has_space_indents == 1
	  return 0
  endif
  return 1 " Default indent style for empty files is Tab.
endfunction

" Check current buffer and configure for tab or space indents.
function ftplugin#python#PyIndentAutoCfg()
  if ftplugin#python#PyIsTabIndent()
    set noexpandtab
  else
    set expandtab
  endif
endfunction
