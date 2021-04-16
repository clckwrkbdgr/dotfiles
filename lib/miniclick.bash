# Parses arguments in very simple way.
# Does not alter require global state so may be re-used.
# Useful for stand-alone functions.
#
# Example of usage:
# my_function() {
#    miniclick positional1 positional2 --option --default-option --another-option -- "$@"
#    echo $positional1 # foo (see below)
#    echo $positional2 # bar
#    echo $option # option_value
#    echo $default_option # <empty>
#    echo $another_option # another_value
# }
#
# my_function 'foo' 'bar' 'option_value' --another-option='another_value'

. "$XDG_CONFIG_HOME/lib/utils.bash"

miniclick() {
	# Params: <positionals...> -- <keyword args...> -- "$@"
	# E.g.: 'short' 'long' 'name' -- 'default' 'epilog' 'help' -- "$@"
	# Sets variables with corresponding names.
	# Expects command line with positionals fully filled first,
	# and then keyword arguments:
	# - either passed as potisionals in order of definition,
	# - or passed as double-dashes named arguments: --arg=<value> in any order
	# WARNING: Both double-dashed delimiters should be present
	#          even if positionals or keywords are not required!
	# Missing arguments are silently ignored and become unset.
	# It can be tested e.g. with [ -z "${argname+x}" ] to check if arg is set.
	# E.g.: -o --option option_name --epilog='' --help=Description
	# will result in:
	#   short=-o
	#   long=--option
	#   name=option_name
	#   default=  (actually unset)
	#   epilog=   (set but empty)
	#   help=Message
	# Any unknown extra argument will result in panic.
	declare -a _miniargs
	declare -a _minikwargs

	while [ -n "$1" -a "$1" != '--' ]; do
		local _name="$1"
		if startswith "$_name" '--'; then
			local _name=${_name##--}
			_minikwargs+=("${_name}")
			eval "unset ${_name}"
		else
			_miniargs+=("${_name}")
			eval "${_name}=''"
		fi
		shift
	done
	[ -z "$1" ] && panic "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: miniclick: cannot find double-dash marker for arguments!"
	shift

	_current_arg=0
	_current_kwarg=0
	for arg in "$@"; do
		if [ -n "$_current_arg" ]; then
			# Escaping value as it may contain single quote: ..'.. => ..'"'"'..
			eval "${_miniargs[$_current_arg]}='"${arg//\'/\'\"\'\"\'}"'"
			_current_arg=$((_current_arg+1))
			if [ $_current_arg -ge ${#_miniargs[@]} ]; then
				_current_arg=''
			fi
			continue
		fi
		if [ -n "$_current_kwarg" ]; then
			for _kwarg in "${_minikwargs[@]}"; do
				_doubledashed="--${_kwarg}="
				if startswith "$arg" "$_doubledashed"; then
					arg=${arg##$_doubledashed}
					eval "${_kwarg}='$arg'"
					break
				fi
				_doubledashed=""
			done
			[ -n "$_doubledashed" ] && continue

			eval "${_minikwargs[$_current_kwarg]}='$arg'"
			_current_kwarg=$((_current_kwarg+1))
			if [ $_current_kwarg -ge ${#_minikwargs[@]} ]; then
				_current_kwarg=''
			fi
			continue
		fi
		panic "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: miniclick: unknown unnamed param: '$arg'"
	done
}


