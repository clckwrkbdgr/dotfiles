# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

update_xterm_title() {
	echo -en "\033]0;${1}\a"
}

# User specific aliases and functions
if env | grep -q VIMRUNTIME; then IS_VIM="(vim)"; else IS_VIM=""; fi
export EDITOR=vim
export PAGER=less
export PATH=$PATH:/opt/android-sdk-linux/tools:/opt/android-sdk-linux/platform-tools
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
export PS1="\[\033[1;37m\]${IS_VIM}\W\$\[\033[0m\] \033]0;\w\a" # (vim)\W\$   also sets xterm title to \w
export PS2="\[\033[1;37m\]>\[\033[0m\] " # >
export PS4="\[\033[1;37m\]+\[\033[0m\] " # +
export LC_COLLATE=C # For `ls' not to mix upper and lower case letters.
export SDL_VIDEO_CENTERED=1
export GREP_OPTIONS='--color=auto'
export GREP_COLOR='1;32'
export HISTCONTROL=ignoredups
source ~/.bash_vars
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'
alias ls='ls --color -F'
alias rss='ranger ~/RSS'
alias shuffle='find "$@" -type f | sort -R | tail'
alias winedesktop='wine explorer /desktop=name,1024x768'

eval `dircolors ~/.dir_colors`
xmodmap -e 'keycode 65 = space underscore'
