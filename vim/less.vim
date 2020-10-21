"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Emulates pager (less/more) behavior.
" Put it to $VIMRUNTIME/vimfiles/extended/
"   OR
" Put following line to $VIMRUNTIME/vimfiles/extended/:
"     source <config_path>/less.vim
" and run vim with -c 'runtime extended/less.vim'
set nocompatible
set laststatus=0
set cmdheight=1
set nomodifiable
set readonly
nmap b <C-B><C-G>
nmap q :q!<CR>
nmap k <C-Y>
nmap j <C-E>
nmap <Esc> :q!<CR>
nmap <End> G
nmap <Home> gg
" Apparently this is binding for space:
nmap   <C-F><C-G>

" Remember last position.
if has("autocmd")
  au BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
endif
