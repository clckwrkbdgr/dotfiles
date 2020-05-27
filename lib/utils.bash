panic() { # <message text>
	# Prints message to stderr and terminates the script.
	echo "$@" >&2
	exit 1
}

finally_init () {
	local next="$1"
	eval "finally () {
		local oldcmd='$(echo "$next" | sed -e s/\'/\'\\\\\'\'/g)'
		local newcmd=\"\$oldcmd; \$1\"
		trap -- \"\$newcmd\" 0
		finally_init \"\$newcmd\"
	}"
}
finally_init true
