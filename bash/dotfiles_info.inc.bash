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

dotfiles_info() {
	local -A known_dotfiles
	# Default XDG dir entries.
	known_dotfiles[.config]=
	known_dotfiles[.cache]=
	known_dotfiles[.local]=
	# Hardcoded entries.
	known_dotfiles[.bashrc]=
	known_dotfiles[.profile]=
	known_dotfiles[.ssh]=
	# Custom extensions to XDG.
	known_dotfiles[.state]=
	known_dotfiles[.cloud]=

	while IFS='\n' read line; do
		[[ -z "$line" ]] && continue
		local comment="^ *#.*$"
		[[ "$line" =~ $comment ]] && continue
		local name=${line%=*}
		local value=${line##*=}
		known_dotfiles["$name"]="$value"
	done <"$XDG_CONFIG_HOME/dotfiles_info.cfg"

	if [ -f ~/.local/dotfiles_info.cfg ]; then
		# TODO complete duplication of the loop above, but cannot use pipes because of array inside the loop.
		while IFS='\n' read line; do
			[[ -z "$line" ]] && continue
			local comment="^ *#.*$"
			[[ "$line" =~ $comment ]] && continue
			local name=${line%=*}
			local value=${line##*=}
			known_dotfiles["$name"]="$value"
		done <~/.local/dotfiles_info.cfg
	fi

	local known=()
	local unknown=0
	for dotfile in .?*; do
		[ "$dotfile" == '..' ] && continue
		if [ ${known_dotfiles[$dotfile]+true} ]; then
			local name="${known_dotfiles[$dotfile]}"
			[ -n "$XDG_DOTFILES_VERBOSE" ] && echo "Known as [$name]: $dotfile" >&2
			for i in "${known[@]}"; do
				if [ "$i" == "[$name]" ]; then
					name=''
					break;
				fi
			done
			if [ -n "$name" ]; then
				known+=("[$name]")
			fi
		else
			[ -n "$XDG_DOTFILES_VERBOSE" ] && echo "Unknown: $dotfile" >&2
			unknown=$((unknown+1))
		fi
	done
	if [ $unknown -gt 0 ]; then
		known+=("[.$unknown]")
	fi

	(IFS=''; echo "${known[*]}")
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
	if [ "$1" == '-v' ]; then
		XDG_DOTFILES_VERBOSE=true
	fi

	dotfiles_info
fi
