# Bash Prompt management.
# Treats PS1 as a sequence of (colored) sections,
# each section is either:
# - a function or shell command;
# - builtin PS1 special characters, like \W or \u.
# Each section may have own color (see lib/colors.bash).
# Resulting PS1 will always have \$ at the end and a single trailing space: "...$ "
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/colors.bash"
. "$XDG_CONFIG_HOME/lib/arrays.bash"

declare -a _old_PS1

prompt::clear() {
	# Clears PS1 of all sections..
	# Compiled value will still be "$ ".
	unset _prompt_sections
	unset _prompt_colors
	declare -a _prompt_sections
	declare -a _prompt_colors
	prompt::refresh
}

prompt::append_section() {
	# Appends new section to the end of the sequence.
	# Params: <function or PS1 special char> [<name of the color>]
	# For colors see lib/colors.bash
	local section="$1"
	local color="$2"
	arrays::append _prompt_sections "$section"
	arrays::append _prompt_colors "$color"
	prompt::refresh
}

prompt::prepend_section() {
	# Inserts new section to the beginning of the sequence.
	# Params: <function or PS1 special char> [<name of the color>]
	# For colors see lib/colors.bash
	local section="$1"
	local color="$2"
	_prompt_sections=("$section" "${_prompt_sections[@]}")
	_prompt_colors=("$color" "${_prompt_colors[@]}")
	prompt::refresh
}

prompt::delete_section() {
	# Deletes section from the sequence.
	# Params: <function or PS1 special char>
	local section="$1"
	for i in "${!_prompt_sections[@]}"; do
		if [[ "${_prompt_sections[i]}" = "$section" ]]; then
			unset '_prompt_sections[i]'
		fi
	done
	prompt::refresh
}

prompt::refresh() {
	# Refreshes PS1 using defined sections.
	# Normally isn't needed to be called manually, as other prompt::* functions refresh PS1 automatically.
	# Resulting PS1 will always have \$ at the end and a single trailing space: "...$ "
	arrays::append _old_PS1 "$PS1"

	_ps_generated=''
	for _index in "${!_prompt_sections[@]}"; do
		local section="${_prompt_sections[_index]}"
		local color="${_prompt_colors[_index]}"
		if [ -n "$color" ]; then
			local color_value="${!color}"
			_ps_generated="${_ps_generated}\[$color_value\]"
		fi
		if startswith "$section" '\'; then
			_ps_generated="${_ps_generated}$section"
		else
			_ps_generated="${_ps_generated}\$($section)"
		fi
		if [ -n "$color" ]; then
			_ps_generated="${_ps_generated}\[${reset_color}\]"
		fi
	done
	default_PS1="\[$bold_white\]\$\[$reset_color\] "
	export PS1="${_ps_generated}${default_PS1}"
}
