# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# User specific aliases and functions
if env | grep -q VIMRUNTIME; then IS_VIM="(vim)"; else IS_VIM=""; fi
export EDITOR=vim
export PAGER=less
export PATH=$PATH:/opt/android-sdk-linux/tools:/opt/android-sdk-linux/platform-tools
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
export PS1="\[\033[1;37m\]${IS_VIM}\W\$\[\033[0m\] " # \W\$
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
alias rss='ranger ~/rss'
alias mplayerrotate='mplayer -vo xv -vf rotate'
alias mediasort='mediasort --root_dir=/x/music'
alias vk='vksearch --count=1 --save-to=/tmp --play'
alias shuffle='find "$@" -type f | sort -R | tail'

xmodmap -e 'keycode 65 = space underscore'

ps aux | grep lastfmsubmitd | grep -qv grep || echo 'lastfmsubmitd is down! <sudo service lastfmsubmitd restart>'
mailx -H -S headline="%d - %100s" 2>&1 | grep -v 'No mail for '$USERNAME
