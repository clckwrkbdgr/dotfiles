# Friendly argument parser for command-line bash sripts
# Works like click package for Python.
#
# Example of usage:
# click::command bash_function 'Does the thing'
# click::epilog 'Epilog will be displayed at the bottom of the usage info'
# click::option '-o' '--option' 'option_name' 'default value' 'Help message for option'
# click::flag '-f' '--flag' 'flag_name' 'Help message for flag'
# click::argument 'arg_name' 'Help message for argument'
# bash_function() {
#    # Here you can access associative array ${CLICK_ARGS[option_name]} etc.
#    # Call click::usage to print usage.
# }
# 
# # Reads and parses CLI arguments, prepares CLICK_ARGS and calls click::command function.
# # Exits the script with rc of that function.
# click::run "$@"
#
# Flags '-h' and '--help' are built-in and print command-line usage info based on registered arguments.
#
# NOTE: There might be only one main click::command in the whole shell instance.
#       If two commands are initiated, the result is undefined!

. "$XDG_CONFIG_HOME/lib/utils.bash"

_click_command=''
_click_command_help=''
_click_command_epilog=''
declare -A _click_type # 'flag', 'option', 'argument'
declare -A _click_help
declare -A _click_short
declare -A _click_long
_click_narg_argument='' # Name of argument with nargs=-1
declare -A _click_default
_click_positional_count=0
declare -A _click_arg_pos

click::miniclick() {
	# Parses arguments in very simple way.
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
	while [ -n "$1" -a "$1" != '--' ]; do
		_miniargs+=("$1")
		eval "$1=''"
		shift
	done
	[ -z "$1" ] && panic "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: miniclick: cannot find first double-dashed separator!"
	shift
	declare -a _minikwargs
	while [ -n "$1" -a "$1" != '--' ]; do
		_minikwargs+=("$1")
		eval "unset $1"
		shift
	done
	[ -z "$1" ] && panic "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: miniclick: cannot find second double-dashed separator!"
	shift
	_current_arg=0
	_current_kwarg=0
	for arg in "$@"; do
		if [ -n "$_current_arg" ]; then
			eval "${_miniargs[$_current_arg]}='$arg'"
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

click::command() {
	# Registers main command function.
	# Params: <main command callback> <help>
	# E.g.: 'shell_function' 'The purpose of the script.'
	# Callback must be a real shell function, may be defined at any point but before call to click::run
	# Help message may contain escaped symbols compatible with 'echo -e'
	[ -z "$1" ] && panic 'click::command did not receive an argument!'
	_click_command="$1"
	_click_command_help="${_click_command_help}${_click_command_help:+\n}$2"
}

click::epilog() {
	# Adds text to epilog.
	# Params: <text>
	# It will be appended to any already exiting epilog, so epilog calls may stack:
	#   click::epilog 'First line'
	#   click::epilog 'Second line\nThird line'
	# Epilog message may also contain escaped symbols compatible with 'echo -e'
	[ -z "$1" ] && panic 'click::epilog did not receive an argument!'
	_click_command_epilog="$1"
}

click::flag() {
	# Registers flag argument (true/false)
	# Params: <short> <long> <name> --help=<help>
	#     Or: <short> <long> <name> <help>
	# E.g.:   '-f' '--flag' 'flag_name' 'Sets flag.'
	# If flag name is empty, long option name is used if present, short option char otherwise.
	# Parsed flag argument in CLICK_ARGS is empty (by default) or non-empty when specified.
	# Use test [ -n "${CLICK_ARGS[flag_name]}" ]
	# Help message may contain escaped symbols compatible with 'echo -e'
	click::miniclick 'short' 'long' 'name' -- help -- "$@"

	short_re='^-[A-Za-z0-9]$'
	[ -z "$short" ] && panic 'Short flag is required!'
	[[ "${short}" =~ $short_re ]] || panic "Expected short flag in format '-<single char>', got instead: '${short}'"

	if [ -n "$long" ]; then
		long_re='^--[A-Za-z0-9][A-Za-z0-9_-]+$'
		[[ "${long}" =~ $long_re ]] || panic "Expected long flag in format '--<name>', got instead: '${long}'"
	fi

	if [ -z "$name" ]; then
		if [ -n "$long" ]; then
			name=${long#--}
		else
			name=${short#-}
		fi
	fi
	# TODO: required flags
	_click_type["$name"]='flag'
	_click_help["$name"]="$help"
	_click_short["$name"]="$short"
	_click_long["$name"]="$long"
}

click::option() {
	# Registers option argument (with value).
	# Params: <short> <long> <name> --default=<default> --help=<help>
	#     Or: <short> <long> <name> <default> <help>
	# E.g.:   '-o' '--option' 'option_name' 'nothing' 'Description of the option behavior.'
	# If option name is empty, long option name is used if present, short option char otherwise.
	# If option was not specified at command line, CLICK_ARGS will contain default value.
	# Help message may contain escaped symbols compatible with 'echo -e'
	click::miniclick 'short' 'long' 'name' -- default help -- "$@"

	[ -z "$short" ] && panic 'Short option is required!'
	short_re='^-[a-z0-9]$'
	[[ "${short}" =~ $short_re ]] || panic "Expected short option in format '-<single char>', got instead: '${short}'"

	if [ -n "$long" ]; then
		long_re='^--[a-z0-9][a-z0-9_-]+$'
		[[ "${long}" =~ $long_re ]] || panic "Expected long option in format '--<name>', got instead: '${long}'"
	fi

	if [ -z "$name" ]; then
		if [ -n "$long" ]; then
			name=${long#--}
		else
			name=${short#-}
		fi
	fi

	# TODO: required options
	# TODO: multi values (nargs)
	# TODO: predefined list of choices
	_click_type["$name"]='option'
	_click_help["$name"]="$help"
	_click_short["$name"]="$short"
	_click_long["$name"]="$long"
	_click_default["$name"]="$default"
}

click::argument() {
	# Registers positional argument.
	# Params: <name> --nargs=-1 --default=<default_value> --help=<help>
	#     Or: <name> <help>
	# E.g.:   'filename' 'Name of the input file.'
	# All positionals must be consumed.
	# Exceptions are only arguments with default values.
	# If argument is missing, default value is taken,
	# but only if there is no futher arguments at all.
	# Default value can be empty (--default=''). In this case argument is still considered not required and will be initialiazed with empty value.
	#
	# The only valid value for nargs is -1 (or default empty value).
	# There can be only one argument with nargs=-1 and it should be the last argument.
	# It will consume all arguments till the end.
	#
	# Help message may contain escaped symbols compatible with 'echo -e'
	click::miniclick 'name' -- help nargs default -- "$@"

	[ -z "$name" ] && panic 'Argument name is required!'
	[ -n "$nargs" -a "$nargs" != '-1' ] && panic "Parameter nargs supports only value -1 for arguments: $name nargs=$nargs"
	[ -n "$_click_narg_argument" ] && panic "There was already defined an argument with nargs=-1: $_click_narg_argument"

	if [ "$nargs" == '-1' ]; then
		_click_narg_argument="$name"
	fi
	_click_type["$name"]='argument'
	_click_help["$name"]="$help"
	if [ -n "${default+has_value}" ]; then
		_click_default["$name"]="$default"
	fi
	_click_arg_pos["$name"]="${_click_positional_count}"
	_click_positional_count=$((_click_positional_count + 1))
}

# TODO groups like click.group() for subcommands

click::usage() {
	# Prints usage message.
	usage="$0"
	for name in "${!_click_type[@]}"; do
		if [ ${_click_type[$name]} == 'option' -o ${_click_type[$name]} == 'flag' ]; then
			usage="$usage [${_click_short[$name]}]"
		fi
	done
	for name in "${!_click_type[@]}"; do
		if [ ${_click_type[$name]} == 'argument' ]; then
			usage="$usage <$name>"
		fi
	done
	echo "Usage: $usage"
	if [ -n "${_click_command_help}" ]; then
		echo -e "${_click_command_help}"
	fi
	if [ "${#_click_type[@]}" -ne 0 ]; then
		echo 'Parameters:'
	fi
	for name in "${!_click_type[@]}"; do
		if [ ${_click_type[$name]} == 'option' -o ${_click_type[$name]} == 'flag' ]; then
			echo -n "  ${_click_short[$name]}"
			if [ -n "${_click_long[$name]}" ]; then
				echo -n ", ${_click_long[$name]}"
			fi
			echo
		elif [ ${_click_type[$name]} == 'argument' ]; then
			echo "  <$name>"
		fi
		echo -e "${_click_help[$name]}" | sed 's/^/        /' # FIXME this is the only external command in the whole file.
		if [ ${_click_type[$name]} == 'option' ]; then
			echo "        Default is '${_click_default[$name]}'."
		elif [ ${_click_type[$name]} == 'argument' ]; then
			if [ -n "${_click_default[$name]}" ]; then
				echo "        Default is '${_click_default[$name]}'."
			fi
		elif [ ${_click_type[$name]} == 'flag' ]; then
			echo "        Default is false."
		fi
	done
	if [ -n "${_click_command_epilog}" ]; then
		echo -e "${_click_command_epilog}"
	fi
}

# Main associative array of collected CLI args.
# Access: ${CLICK_ARGS[arg_name]}
declare -A CLICK_ARGS

# Sequence of values for argument with nargs=1 if there was one.
# Access: ${CLICK_NARGS[i]}
# Total number: ${#CLICK_NARGS[@]}
# Iterate over: ${CLICK_NARGS[@]}
declare -a CLICK_NARGS

click::run() {
	# Parses CLI arguments, calls registered command.
	# Usage: <list of arguments>
	# Any set of arguments can be passed.
	# Pass "$@" from the main script for real CLI args.
	if [ "$(LC_ALL=C type -t "${_click_command}")" != 'function' ]; then
		panic "click::command does not point to an existing shell function: '${_click_command}'" >&2
	fi

	for name in "${!_click_type[@]}"; do
		CLICK_ARGS["$name"]="${_click_default[$name]}"
	done
	current_arg_pos=0
	option_re='^-.+'
	while [ -n "$1" ]; do
		arg="$1"
		matched=''
		if [ "$arg" == '-h' -o "$arg" == '--help' ]; then
			click::usage >&2
			exit 0
		fi
		if [ "${#CLICK_NARGS[@]}" -gt 0 ]; then
			CLICK_NARGS+=("$1")
			name="$_click_narg_argument"
			CLICK_ARGS["$name"]="${CLICK_ARGS["$name"]} $1"
			matched=true
		elif [[ "$arg" =~ $option_re ]]; then
			for name in "${!_click_type[@]}"; do
				if [ ${_click_type[$name]} == 'flag' ]; then
					if [ "${_click_short[$name]}" == "$arg" ]; then
						CLICK_ARGS["$name"]='true'
						matched=true
						break
					elif [ "${_click_long[$name]}" == "$arg" ]; then
						CLICK_ARGS["$name"]='true'
						matched=true
						break
					fi
				elif [ ${_click_type[$name]} == 'option' ]; then
					if [ "${_click_short[$name]}" == "$arg" ]; then
						shift # TODO: check that next value is present and is a value, not an option key.
						CLICK_ARGS["$name"]="$1"
						matched=true
						break
					elif [ "${_click_long[$name]}" == "$arg" ]; then
						shift # TODO: check that next value is present and is a value, not an option key.
						CLICK_ARGS["$name"]="$1"
						matched=true
						break
					fi
				fi
			done
		else
			for name in "${!_click_type[@]}"; do
				if [ ${_click_type[$name]} == 'argument' ]; then
					if [ ${_click_arg_pos[$name]} == "$current_arg_pos" ]; then
						if [ "$_click_narg_argument" == "$name" ]; then
							CLICK_NARGS+=("$1")
							if [ -n "${CLICK_ARGS["$name"]}" ]; then
								CLICK_ARGS["$name"]="${CLICK_ARGS["$name"]} $1"
							else
								CLICK_ARGS["$name"]="$1"
							fi
						else
							CLICK_ARGS["$name"]="$1"
							current_arg_pos=$((current_arg_pos + 1))
						fi
						matched=true
						break
					fi
				fi
			done
		fi
		if [ -z "$matched" ]; then
			echo "Unknown argument: $arg" >&2
			click::usage >&2
			exit 1
		fi
		shift
	done
	if [ "${#CLICK_NARGS[@]}" -gt 0 ]; then
		current_arg_pos=$((current_arg_pos + 1))
	fi
	while [ $current_arg_pos -lt ${_click_positional_count} ]; do
		for name in "${!_click_type[@]}"; do
			if [ ${_click_type[$name]} == 'argument' ]; then
				if [ ${_click_arg_pos[$name]} == "$current_arg_pos" ]; then
					if [ -n "${_click_default[$name]+has_value}" ]; then
						CLICK_ARGS["$name"]="${_click_default[$name]}"
						break
					else
						panic "Positional argument is expected: '$name'"
					fi
				fi
			fi
		done
		current_arg_pos=$((current_arg_pos + 1))
	done

	"${_click_command}"
	exit $?
}
