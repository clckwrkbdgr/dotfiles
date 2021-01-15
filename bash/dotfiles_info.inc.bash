#!/bin/bash
# Analyzes dotfiles in the current dir and informs about known/unknown ones.
# Groups known dotfiles and marks them under one group name: [group]
# Unknown dotfiles are calculated into single value: [.1]
# Prints string value suitable for use in PS1: [group][.1]
#
# Set XDG_DOTFILES_VERBOSE to produce debug output.
# Uses following data sources for known :
# - Built-in entries: XDG dirs, some legacy values etc.
# - Main data file: $XDG_CONFIG_HOME/dotfiles_info.cfg
# - User data file: ~/.local/dotfiles_info.cfg
# File format is <filename>=<group name>, comments start with '#'
# Group name can be empty.

case "$BASH_VERSION" in
   3.*)
      . "$XDG_CONFIG_HOME/bash/dotfiles_info.3.inc.bash"
      ;;
   *)
      . "$XDG_CONFIG_HOME/bash/dotfiles_info.default.inc.bash"
      ;;
esac
export -f dotfiles_info

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
	if [ "$1" == '-v' ]; then
		XDG_DOTFILES_VERBOSE=true
	fi

	dotfiles_info
fi
