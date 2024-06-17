#!/bin/sh
[ -f ~/.config/bash/debug.inc.bash ] && . ~/.config/bash/debug.inc.bash

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

_grep_version=$(grep -V 2>/dev/null | head -1 | sed 's/.* \([0-9][0-9.]*\)$/\1/' | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }')
if [ "${_grep_version}" -ge 3008000000 ]; then
	export GREP_COLORS='mt=1;32'
else
	export GREP_COLOR='1;32'
fi
unset _grep_version

export WINEPREFIX=/opt/wine-$USER
export QT_STYLE_OVERRIDE=kvantum
if [ -n "$PYTHONPATH" ]; then
	export PYTHONPATH="$HOME/.local/lib:$HOME/.config/lib:$PYTHONPATH"
else
	export PYTHONPATH="$HOME/.local/lib:$HOME/.config/lib"
fi
export PYTHONWARNINGS=always::DeprecationWarning,ignore:DEPRECATION::pip._internal.cli.base_command
_clckwrkbdgr_debug_profile "After initial exports."

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
_clckwrkbdgr_debug_profile "Loaded XDG configuration."

# User/platform/host specific settings.
_osname=`uname`
_hostname=`hostname`
_clckwrkbdgr_debug_profile "Read os/host names."

[ -f "$XDG_CONFIG_HOME/local/profile" ] && . "$XDG_CONFIG_HOME/local/profile"
_clckwrkbdgr_debug_profile "Checked XDG_CONFIG_HOME/local profile"
[ -f "$XDG_CONFIG_HOME/local/profile.${_osname}" ] && . "$XDG_CONFIG_HOME/local/profile.${_osname}"
_clckwrkbdgr_debug_profile "Checked XDG_CONFIG_HOME/local os-specific profile"
[ -f "$XDG_CONFIG_HOME/local/profile.${_hostname}" ] && . "$XDG_CONFIG_HOME/local/profile.${_hostname}"
_clckwrkbdgr_debug_profile "Checked XDG_CONFIG_HOME/local host-specific profile"

[ -f "$XDG_DATA_HOME/profile" ] && . "$XDG_DATA_HOME/profile"
_clckwrkbdgr_debug_profile "Checked XDG_DATA_HOME profile"
[ -f "$XDG_DATA_HOME/profile.${_osname}" ] && . "$XDG_DATA_HOME/profile.${_osname}"
_clckwrkbdgr_debug_profile "Checked XDG_DATA_HOME os-specific profile"
[ -f "$XDG_DATA_HOME/profile.${_hostname}" ] && . "$XDG_DATA_HOME/profile.${_hostname}"
_clckwrkbdgr_debug_profile "Checked XDG_DATA_HOME host-specific profile"

[ -f ~/.local/profile ] && . ~/.local/profile
_clckwrkbdgr_debug_profile "Checked ~/.local profile"
[ -f ~/.local/profile.${_osname} ] && . ~/.local/profile.${_osname}
_clckwrkbdgr_debug_profile "Checked ~/.local os-specific profile"
[ -f ~/.local/profile.${_hostname} ] && . ~/.local/profile.${_hostname}
_clckwrkbdgr_debug_profile "Checked ~/.local host-specific profile"

# For interactive login shell it's better to source shell rc.
if [ -n "$BASH_VERSION" ]; then
	case :$SHELLOPTS: in
		*:posix:*) export BASH_POSIX_MODE=on ;;
	esac
fi
if [ -n "$BASH_VERSION" -a -z "$BASH_POSIX_MODE" ]; then
	if [ -n "$PS1" ]; then
		if [ -f "$HOME/.bashrc" ]; then
			. "$HOME/.bashrc"
		fi
	fi
fi
_clckwrkbdgr_debug_profile "Loaded .bashrc"

# Optionally run custom shell command instead of $SHELL.
# Variable expands without quotes as list of tokens, so spaces in arguments should be properly escaped.
if [ -n "$CUSTOM_SHELL_COMMAND" ]; then
	if [ -z "$CUSTOM_SHELL_OPENED" ]; then
		export CUSTOM_SHELL_OPENED=1
		exec ${CUSTOM_SHELL_COMMAND}
	fi
fi
