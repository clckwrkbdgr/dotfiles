# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Section for XDG directory support.
. .config/bin/xdg


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
