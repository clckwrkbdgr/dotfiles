# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Section for XDG directory support.
XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$HOME/.config}
XDG_CACHE_HOME=${XDG_CACHE_HOME:-$HOME/.cache}
XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}
xrdb -load ~/.config/Xresources
export XAUTHORITY="$XDG_RUNTIME_DIR/Xauthority"
export ICEAUTHORITY="$XDG_RUNTIME_DIR/ICEauthority"
export GIMP2_DIRECTORY="$XDG_CONFIG_HOME/gimp"
export LESSHISTFILE="$XDG_CACHE_HOME/less/history"
export MPLAYER_HOME="$XDG_CONFIG_HOME/mplayer"
#export WINEPREFIX="$XDG_DATA_HOME/wine"
alias mocp='mocp -M "$XDG_CONFIG_HOME/moc"'
export RLWRAP_HOME="$XDG_CACHE_HOME/rlwrap_history"
alias svn='svn --config-dir "$XDG_CONFIG_HOME/subversion"'
export VIMPERATOR_INIT=":source $XDG_CONFIG_HOME/vimperator/vimperatorrc"
export VIMPERATOR_RUNTIME="$XDG_CONFIG_HOME/vimperator"
export HISTFILE="$XDG_CACHE_HOME/bash/history"
mkdir -p "$XDG_CACHE_HOME/vim"
export VIMINIT='let $MYVIMRC="'"$XDG_CONFIG_HOME"'/vim/vimrc" | source $MYVIMRC'

# User specific aliases and functions
if env | grep -q VIMRUNTIME; then IS_VIM="(vim)"; else IS_VIM=""; fi
export EDITOR=vim
export PAGER=less
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
export LC_COLLATE=C # For `ls' not to mix upper and lower case letters.
export SDL_VIDEO_CENTERED=1
export GREP_OPTIONS='--color=auto'
export GREP_COLOR='1;32'
export HISTCONTROL=ignoredups
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'
alias ls='ls --color -F'
alias shuffle='find "$@" -type f | sort -R | tail'
eval `dircolors "$XDG_CONFIG_HOME/dir_colors"`

# Prompt
count_dotfiles() {
	NUMBER=$(find -maxdepth 1 -mindepth 1 -name '.*' | wc -l)
	[ $NUMBER -gt 0 ] && echo "[.$NUMBER]"
}
WHITE="\[\033[1;37m\]"
RED="\[\033[1;31m\]"
NORMAL="\[\033[0m\]"
xterm_title() { echo "\033]0;$1\a"; }
export PS1="${RED}\$(count_dotfiles)${WHITE}${IS_VIM}\W\$${NORMAL} $(xterm_title \\w)"
export PS2="${WHITE}>${NORMAL} " # >
export PS4="${WHITE}+${NORMAL} " # +
unset WHITE RED NORMAL

# User private settings.
[ -f ~/.profile.local ] && source ~/.profile.local
