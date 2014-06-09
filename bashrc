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

function alarm() {
	if [ -n "$1" ]; then
		echo 'alert Alarm' | at $@;
	else
		alert Alarm
	fi
}

function seen() {
	ls -R --color=auto
	F=$(find . \! -executable | sort -nk 2 | egrep '(ogm|avi|mkv|mp4|wmv|mpg|mov)$' | head -1)
	YES="$1"
	if [ -z "$YES" ]; then
		echo ${F}, continue?
		read YES
	fi
	if [ "$YES" = "y" ]; then
		mplayer $@ "$F" && chmod a+x "$F"
	fi
}

df | while read L; do
	[ "$(echo $L | sed 's/.* \([^ ]\+\)% .*/\1/' | sed 's/[^0-9]/0/g' )" -gt 98 ] && echo $L | sed 's/.* \([^ ]\+%\)/\1/';
done
ps aux | grep lastfmsubmitd | grep -qv grep || echo 'lastfmsubmitd is down! <sudo service lastfmsubmitd restart>'
python3 ~/motd.py
[ "$(du /var/mail/$USERNAME | cut -f 1)" -gt 0 ] && echo "New mailx!"
