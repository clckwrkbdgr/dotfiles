# Current subshell info: parent processes, shells, terminals etc.
. "$XDG_CONFIG_HOME/lib/prompt.bash"

_PS_in_vim() {
	[ -n "$VIMRUNTIME" ] && echo "(vim)"
}

if [ -n "$FIX_SHLVL" ]; then # Resets current shlvl to be treated as zero. Each subshell will start to add 1 level as expected.
	_DISPLAY_SHLVL=$((SHLVL-FIX_SHLVL))
elif [ -z "$_DISPLAY_SHLVL" ]; then # TODO instead of this there should be a shlvl::reset and some var to subtract, like for screen or tmux invocations.
	_DISPLAY_SHLVL=$((SHLVL-2)) # For GUI interactive shells: 1 for GUI + 1 for terminal
fi

_PS_shlvl() {
	if [ "$_DISPLAY_SHLVL" -gt 0 ]; then
		echo "(bash+$_DISPLAY_SHLVL)"
	fi
}

_PS_ranger() {
	[ -z "$RANGER_LEVEL" ] && return
	fixed_ranger_level=$((RANGER_LEVEL-1))
	if [ "$fixed_ranger_level" -gt 0 ]; then
		echo "(ranger+$fixed_ranger_level)"
	else
		echo "(ranger)"
	fi
}

_PS_tmux() {
	if [ -n "$TMUX" ]; then
		echo "(tmux)"
	fi
}

prompt::clear
prompt::append_section _PS_in_vim bold_red
prompt::append_section _PS_shlvl bold_red
prompt::append_section _PS_ranger bold_red
prompt::append_section _PS_tmux bold_red

# Current dir state/info.
. "$XDG_CONFIG_HOME/bash/dotfiles_info.inc.bash"
prompt::prepend_section dotfiles_info bold_yellow

# Main prompt settings.
prompt::append_section '\W' bold_white

PS2=">"
export PS2="\[${bold_white}\]${PS2}\[${reset_color}\] "

PS4="+"
export PS4="\[${bold_white}\]${PS4}\[${reset_color}\] "
