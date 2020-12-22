" To enable the saving and restoring of screen positions.
let g:screen_size_restore_pos = 1
" To save and restore screen for each Vim instance.
" This is useful if you routinely run more than one Vim instance.
" For all Vim to use the same settings, change this to 0.
let g:screen_size_by_vim_instance = 1

" State of the window (maximized/restored)
" Follows shortcut from Alt+Space window menu on Windows,
" which depends on current language. For English it is ma[X]imize/[R]estore.
let g:maximized = "r"

" Unfortunately there is no way to get actual window state
" or even detect Maximize/Restore event, so in order to set global state
" user should call these functions manually.
function! MaximizeWindow()
   " See comment for g:maximized above.
   let g:maximized = "x"
   silent! execute "simalt ~".g:maximized
endfunction
function! RestoreWindow()
   " See comment for g:maximized above.
   let g:maximized = "r"
   silent! execute "simalt ~".g:maximized
endfunction

function! ScreenFilename()
  if has('amiga')
    return "s:.vimsize"
  elseif has('win32')
    return $USERPROFILE.'\_vimsize'
  else
    return $HOME.'/.vimsize'
  endif
endfunction

function! ScreenRestore()
  " Restore window size (columns and lines) and position
  " from values stored in vimsize file.
  " Must set font first so columns and lines are based on font size.
  let f = ScreenFilename()
  if has("gui_running") && g:screen_size_restore_pos && filereadable(f)
    let vim_instance = (g:screen_size_by_vim_instance==1?(v:servername):'GVIM')
    for line in readfile(f)
      let sizepos = split(line)
      if len(sizepos) == 5 && sizepos[0] == vim_instance
        silent! execute "set columns=".sizepos[1]." lines=".sizepos[2]
        silent! execute "winpos ".sizepos[3]." ".sizepos[4]
        return
      endif
      if len(sizepos) == 6 && sizepos[0] == vim_instance
        silent! execute "set columns=".sizepos[1]." lines=".sizepos[2]
        silent! execute "winpos ".sizepos[3]." ".sizepos[4]
        if has('win32')
           silent! execute "simalt ~".sizepos[5]
           let g:maximized = sizepos[5]
        endif
        return
      endif
    endfor
  endif
endfunction

function! ScreenSave()
  " Save window size and position.
  if has("gui_running") && g:screen_size_restore_pos
    let vim_instance = (g:screen_size_by_vim_instance==1?(v:servername):'GVIM')
    let data = vim_instance . ' ' . &columns . ' ' . &lines . ' ' .
          \ (getwinposx()<0?0:getwinposx()) . ' ' .
          \ (getwinposy()<0?0:getwinposy()) . ' ' . g:maximized
    let f = ScreenFilename()
    if filereadable(f)
      let lines = readfile(f)
      call filter(lines, "v:val !~ '^" . vim_instance . "\\>'")
      call add(lines, data)
    else
      let lines = [data]
    endif
    call writefile(lines, f)
  endif
endfunction

if !exists('g:screen_size_restore_pos')
  let g:screen_size_restore_pos = 1
endif
if !exists('g:screen_size_by_vim_instance')
  let g:screen_size_by_vim_instance = 1
endif
if !exists('g:maximized')
  let g:maximized = "r"
endif
autocmd VimEnter * if g:screen_size_restore_pos == 1 | call ScreenRestore() | endif
autocmd VimLeavePre * if g:screen_size_restore_pos == 1 | call ScreenSave() | endif
