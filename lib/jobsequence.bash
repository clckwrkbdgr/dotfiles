#!/bin/bash
# Set of utilities for jobsequence scripts.
# Mostly repeats jobsequence.context and jobsequence.script for shell-based jobsequence scripts.
. "$XDG_CONFIG_HOME/lib/miniclick.bash"

jobsequence_context() {
	# Initiates context for jobsequence script.
	miniclick fake --script_rootdir -- "$@"
	#   script_rootdir - default directory where fixer scripts will be created.
	export JOBSEQUENCE_SCRIPT_ROODIR="${script_rootdir:-$HOME}"
}

jobsequence_script() {
	# Prepares fixer script with given name and optional shebang line.
	# Prints created filename to stdout.
	miniclick script_name shebang -- "$@"

	filename="${JOBSEQUENCE_SCRIPT_ROODIR:-.}/$script_name"
	mkdir -p "$(dirname "$filename")"
	touch "$filename"
	chmod +x "$filename"
	echo "| Created file $filename" >&2
	if [ -n "$shebang" ]; then
		echo "$shebang" >> "$filename"
	fi
	echo "$filename"
}
