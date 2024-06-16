#!/bin/bash
# This is main version for bash >3.*
# See main file `dotfiles.inc.bash` for details.

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

	if [ -f "$XDG_CONFIG_HOME/local/dotfiles_info.cfg" ]; then
		# TODO complete duplication of the loop above, but cannot use pipes because of array inside the loop.
		while IFS='\n' read line; do
			[[ -z "$line" ]] && continue
			local comment="^ *#.*$"
			[[ "$line" =~ $comment ]] && continue
			local name=${line%=*}
			local value=${line##*=}
			known_dotfiles["$name"]="$value"
		done <"$XDG_CONFIG_HOME/local/dotfiles_info.cfg"
	fi

	if [ -f "$XDG_DATA_HOME/dotfiles_info.cfg" ]; then
		# TODO complete duplication of the loop above, but cannot use pipes because of array inside the loop.
		while IFS='\n' read line; do
			[[ -z "$line" ]] && continue
			local comment="^ *#.*$"
			[[ "$line" =~ $comment ]] && continue
			local name=${line%=*}
			local value=${line##*=}
			known_dotfiles["$name"]="$value"
		done <"$XDG_DATA_HOME/dotfiles_info.cfg"
	fi

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
		[ "$dotfile" == '.?*' ] && continue
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
