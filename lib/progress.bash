# Set of routines to display progress state.
#
#   progress::echo "working... /"
#   progress::echo "working... -"
#   progress::echo "working... \\"
#   progress::echo "working... |"
#   progress::clear

progress::echo() { # <echo args...>
	# Behaves like echo, except automatically does not wrap line
	# (implies -n) and clears previous output, so next echo will
	# overwrite the current one, allowing compact display of progress.
	echo -en "\r\033[K"
	echo -n "$@"
}

progress::clear() { # [<echo args...>]
	# Clears all progress status.
	# If args are supplied, additional echo is printed
	# (with proper line ending this time).
	echo -en "\r"
	echo -en "\033[K"
	if [ -n "$1" ]; then
		echo "$@"
	fi
}
