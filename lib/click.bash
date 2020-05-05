# Friendly argument parser for command-line bash sripts
# Works like click package for Python.
#
# Example of usage:
# click::command bash_function 'Does the thing'
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

. "$XDG_CONFIG_HOME/lib/utils.bash"

_click_command=''
_click_help=''
declare -A _click_type # 'flag', 'option', 'argument'
declare -A _click_help
declare -A _click_short
declare -A _click_long
declare -A _click_default
_click_positional_count=0
declare -A _click_arg_pos

click::command() {
	# Registers main command function.
	# Params: <main command callback> <help>
	# E.g.: 'shell_function' 'The purpose of the script.'
	# Callback must be a real shell function, may be defined at any point but before call to click::run
	[ -z "$1" ] && panic 'click::command did not receive an argument!'
	_click_command="$1"
	_click_help="$2"
}

click::flag() {
	# Registers flag argument (true/false)
	# Params: <short> <long> <name> <help>
	# E.g.:   '-f' '--flag' 'flag_name' 'Sets flag.'
	# If flag name is empty, long option name is used if present, short option char otherwise.
	# Parsed flag argument in CLICK_ARGS is empty (by default) or non-empty when specified.
	# Use test [ -n "${CLICK_ARGS[flag_name]}" ]
	short="$1"
	short_re='^-[a-z0-9]$'
	[ -z "$short" ] && panic 'Short flag is required!'
	[[ "${short}" =~ $short_re ]] || panic "Expected short flag in format '-<single char>', got instead: '${short}'"
	long="$2"
	if [ -n "$long" ]; then
		long_re='^--[a-z0-9][a-z0-9_-]+$'
		[[ "${long}" =~ $long_re ]] || panic "Expected long flag in format '--<name>', got instead: '${long}'"
	fi
	name="$3"
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
	# Params: <short> <long> <name> <default> <help>
	# E.g.:   '-o' '--option' 'option_name' 'nothing' 'Description of the option behavior.'
	# If option name is empty, long option name is used if present, short option char otherwise.
	# If option was not specified at command line, CLICK_ARGS will contain default value.
	short="$1"
	[ -z "$short" ] && panic 'Short option is required!'
	short_re='^-[a-z0-9]$'
	[[ "${short}" =~ $short_re ]] || panic "Expected short option in format '-<single char>', got instead: '${short}'"
	long="$2"
	if [ -n "$long" ]; then
		long_re='^--[a-z0-9][a-z0-9_-]+$'
		[[ "${long}" =~ $long_re ]] || panic "Expected long option in format '--<name>', got instead: '${long}'"
	fi
	name="$3"
	if [ -z "$name" ]; then
		if [ -n "$long" ]; then
			name=${long#--}
		else
			name=${short#-}
		fi
	fi
	default="$4"
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
	# Params: <name> <help>
	# E.g.:   'filename' 'Name of the input file.'
	# All positionals must be consumed.
	name="$1"
	[ -z "$name" ] && panic 'Argument name is required!'
	# TODO: nargs
	_click_type["$name"]='argument'
	_click_help["$name"]="$help"
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
	if [ -n "${_click_help}" ]; then
		echo "${_click_help}"
	fi
	for name in "${!_click_type[@]}"; do
		if [ ${_click_type[$name]} == 'option' -o ${_click_type[$name]} == 'flag' ]; then
			echo "${_click_short[$name]}"
			if [ -n "${_click_long[$name]}" ]; then
				echo "${_click_long[$name]}"
			fi
		elif [ ${_click_type[$name]} == 'argument' ]; then
			echo "$name"
		fi
		echo "${_click_help[$name]}"
		if [ ${_click_type[$name]} == 'option' ]; then
			echo "Default is '${_click_default[$name]}'."
		elif [ ${_click_type[$name]} == 'flag' ]; then
			echo "Default is false."
		fi
	done
}

# Main associative array of collected CLI args.
# Access: ${CLICK_ARGS[arg_name]}
declare -A CLICK_ARGS

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
		echo "<$1>"
		arg="$1"
		matched=''
		if [ "$arg" == '-h' -o "$arg" == '--help' ]; then
			click::usage >&2
			exit 0
		fi
		if [[ "$arg" =~ $option_re ]]; then
			for name in "${!_click_type[@]}"; do
				if [ ${_click_type[$name]} == 'flag' ]; then
					if [ ${_click_short[$name]} == "$arg" ]; then
						CLICK_ARGS["$name"]='true'
						matched=true
						break
					elif [ ${_click_long[$name]} == "$arg" ]; then
						CLICK_ARGS["$name"]='true'
						matched=true
						break
					fi
				elif [ ${_click_type[$name]} == 'option' ]; then
					if [ ${_click_short[$name]} == "$arg" ]; then
						shift # TODO: check that next value is present and is a value, not an option key.
						CLICK_ARGS["$name"]="$1"
						matched=true
						break
					elif [ ${_click_long[$name]} == "$arg" ]; then
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
						CLICK_ARGS["$name"]="$1"
						current_arg_pos=$((current_arg_pos + 1))
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
	if [ $current_arg_pos -lt ${_click_positional_count} ]; then
		for name in "${!_click_type[@]}"; do
			if [ ${_click_type[$name]} == 'argument' ]; then
				if [ ${_click_arg_pos[$name]} == "$current_arg_pos" ]; then
					panic "Positional argument is expected: '$name'"
				fi
			fi
		done
	fi

	"${_click_command}"
	exit $?
}
