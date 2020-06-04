# Current subshell info: parent processes, shells, terminals etc.
PS_sub=''
[ -n "$VIMRUNTIME" ] && PS_sub="${PS_sub}(vim)"
if [ -z "$DISPLAY_SHLVL" ]; then
	DISPLAY_SHLVL=$((SHLVL-2)) # For GUI interactive shells: 1 for GUI + 1 for terminal
fi
if [ "$DISPLAY_SHLVL" -gt 0 ]; then
	PS_sub="${PS_sub}(bash+$DISPLAY_SHLVL)"
fi
unset DISPLAY_SHLVL
if [ -n "$RANGER_LEVEL" ]; then
	fixed_ranger_level=$((RANGER_LEVEL-1))
	if [ "$fixed_ranger_level" -gt 0 ]; then
		PS_sub="${PS_sub}(ranger+$fixed_ranger_level)"
	else
		PS_sub="${PS_sub}(ranger)"
	fi
fi
if [ -n "$TMUX" ]; then
	PS_sub="${PS_sub}(tmux)"
fi

# Current dir state/info.
. "$XDG_CONFIG_HOME/bash/dotfiles_info.inc.bash"
PS_dir="\$(dotfiles_info)"

# Main prompt settings.
PS1='\W\$'
PS2=">"
PS4="+"

# Coloring.
. "$XDG_CONFIG_HOME/lib/colors.bash"
export PS1="\[${bold_yellow}\]${PS_dir}\[${bold_red}\]${PS_sub}\[${bold_white}\]${PS1}\[${reset_color}\] "
export PS2="\[${bold_white}\]${PS2}\[${reset_color}\] "
export PS4="\[${bold_white}\]${PS4}\[${reset_color}\] "
