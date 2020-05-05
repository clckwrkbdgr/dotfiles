panic() { # <message text>
	# Prints message to stderr and terminates the script.
	echo "$@" >&2
	exit 1
}

