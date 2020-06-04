. "$XDG_CONFIG_HOME/lib/utils.bash"
deprecated 'Source $XDG_CONFIG_HOME/lib/colors.bash directly instead.'

. "$XDG_CONFIG_HOME/lib/colors.bash"
color::init auto

strip_escape_sequences() {
	deprecated 'Use color::strip from $XDG_CONFIG_HOME/lib/colors.bash instead.'
	color::strip
}
