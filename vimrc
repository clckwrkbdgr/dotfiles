set nocompatible
autocmd BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") |   exe "normal g`\"" | endif
au BufRead,BufNewFile *.md set filetype=markdown
au BufRead,BufNewFile *.tilespec,*.spec set filetype=dosini

map <S-Insert> <MiddleMouse> " Make shift-insert work like in Xterm
map! <S-Insert> <MiddleMouse> " Make shift-insert work like in Xterm
map <C-a> :e %:p:s,.h$,.X123X,:s,.cpp$,.h,:s,.X123X$,.cpp,<CR> " switching between .h and .cpp files that in the SAME directory.
nmap <Space> <PageDown>
nmap <C-L> :make<up><CR>
nmap Q l
nmap QQ :w<CR>
inoremap <C-Space> <C-^>

call pathogen#infect()
set backspace=indent,eol,start " allow backspacing over everything in insert mode
set history=50		" keep 50 lines of command line history
set incsearch		" do incremental searching
set hlsearch
set nobackup
set keymap=russian-jcukenwin " Toggle with C-^
set iminsert=0
set imsearch=0
set iskeyword=@,48-57,_,192-255
set shiftwidth=4
set tabstop=4
set scrolloff=7
set fo+=cr " perhaps will helps with newline after comments.
set foldmethod=syntax " autofolds
set autoindent
set smartindent
set pastetoggle=<F5>
syntax on
nohl

filetype plugin indent on
au FileType python set tabstop=4 | set noexpandtab
let g:xml_syntax_folding=1
au FileType xml setlocal foldmethod=syntax
au FileType html setlocal foldmethod=syntax
