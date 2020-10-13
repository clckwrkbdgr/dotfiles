#!/bin/sh
[ -z "$SHELL" ] && export SHELL=/bin/bash
[ -z "$USER" ] && export USER=$LOGNAME
[ -z "$MAILTO" ] && export MAILTO=$LOGNAME
[ -z "$TERM" ] && export TERM=xterm
[ -z "$DISPLAY" ] && export DISPLAY=:0.0

[ -z "$LC_CTYPE" ] && export LC_CTYPE=en_US.utf8
export LC_COLLATE=C # For `ls' not to mix upper and lower case letters.
[ -z "$MAILPATH" ] && export MAILPATH="/var/mail/$USER"
[ -z "$TEMP" ] && export TEMP=/tmp
export SDL_VIDEO_CENTERED=1
export PYGAME_HIDE_SUPPORT_PROMPT=true
[ -z "$PKG_CONFIG_PATH" ] && export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
export EDITOR=vim
export PAGER=less
export GREP_COLOR='1;32'
export WINEPREFIX=/opt/wine-$USER
if [ -n "$PYTHONPATH" ]; then
	export PYTHONPATH="$HOME/.local/lib:$HOME/.config/lib:$PYTHONPATH"
else
	export PYTHONPATH="$HOME/.local/lib:$HOME/.config/lib"
fi
export PYTHONWARNINGS=ignore:DEPRECATION::pip._internal.cli.base_command,always::DeprecationWarning

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
	PATH="$HOME/bin:$PATH"
fi
if [ -d "$HOME/.config/bin" ] ; then
	PATH="$HOME/.config/bin:$PATH"
fi
if [ -d "$HOME/.local/bin" ] ; then
	PATH="$HOME/.local/bin:$PATH"
fi
export PATH

# Section for XDG directory support.
. ~/.config/lib/xdg.bash
for xdgsourcefile in ~/.config/xdg/*.sh; do
	grep -q '^deprecated' "$xdgsourcefile" && continue # TODO deprecated source files should be removed
	. "$xdgsourcefile"
done

# User/platform/host specific settings.
[ -f ~/.local/profile ] && . ~/.local/profile
[ -f ~/.local/profile.`uname` ] && . ~/.local/profile.`uname`
[ -f ~/.local/profile.`hostname` ] && . ~/.local/profile.`hostname`

# For interactive login shell it's better to source shell rc.
if [ -n "$BASH_VERSION" ]; then
	if [ -n "$PS1" ]; then
		if [ -f "$HOME/.bashrc" ]; then
			. "$HOME/.bashrc"
		fi
	fi
fi

# Optionally run custom shell command instead of $SHELL.
# Variable expands without quotes as list of tokens, so spaces in arguments should be properly escaped.
if [ -n "$CUSTOM_SHELL_COMMAND" ]; then
	if [ -z "$CUSTOM_SHELL_OPENED" ]; then
		export CUSTOM_SHELL_OPENED=1
		exec ${CUSTOM_SHELL_COMMAND}
	fi
fi
