# Friendly argument parser for command-line bash sripts
# Works like click package for Python.
#
# Example of usage:
# click::command bash_function 'Does the thing'
# click::option '-o' '--option' 'option_name' 'default value' 'Help message for option'
# click::flag '-f' '--flag' 'flag_name' 'Help message for flag'
# click::argument 'arg_name' 'Help message for argument'
# bash_function() {
#    # Here you can access associative array ${click::args[option_name]} etc.
#    # Call click::usage to print usage.
# }
# 
# # Reads and parses CLI arguments, prepares click::args and calls click::command function.
# # Exits the script with rc of that function.
# click::run "$@"
#
# Flags '-h' and '--help' are built-in and print command-line usage info based on registered arguments.

. "$XDG_CONFIG_HOME/lib/utils.bash"

click::_command=
click::_help=
declare -A click::_type # 'flag', 'option', 'argument'
declare -A click::_help
declare -A click::_short
declare -A click::_long
declare -A click::_default
click::_positional_count=0
declare -A click::_arg_pos

click::command() {
	# Registers main command function.
	# Params: <main command callback> <help>
	# E.g.: 'shell_function' 'The purpose of the script.'
	# Callback must be a real shell function, may be defined at any point but before call to click::run
	[ -z "$1" ] && panic 'click::command did not receive an argument!'
	click::_command="$1"
	click::_help="$2"
}

click::flag() {
	# Registers flag argument (true/false)
	# Params: <short> <long> <name> <help>
	# E.g.:   '-f' '--flag' 'flag_name' 'Sets flag.'
	# If flag name is empty, long option name is used if present, short option char otherwise.
	# Parsed flag argument in click::args is empty (by default) or non-empty when specified.
	# Use test [ -n "${click::args[flag_name]}" ]
	short="$1"
	[ -z "$short" ] && panic 'Short flag is required!'
	[[ "${short}" =~ '^-[a-z0-9]$' ]] || panic "Expected short flag in format '-<single char>', got instead: '${short}'"
	long="$2"
	if [ -n "$long" ]; then
		[[ "${long}" =~ '^--[a-z0-9][a-z0-9_-]+$' ]] || panic "Expected long flag in format '--<name>', got instead: '${long}'"
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
	click::_type["$name"]='flag'
	click::_help["$name"]="$help"
	click::_short["$name"]="$short"
	click::_long["$name"]="$long"
}

click::option() {
	# Registers option argument (with value).
	# Params: <short> <long> <name> <default> <help>
	# E.g.:   '-o' '--option' 'option_name' 'nothing' 'Description of the option behavior.'
	# If option name is empty, long option name is used if present, short option char otherwise.
	# If option was not specified at command line, click::args will contain default value.
	short="$1"
	[ -z "$short" ] && panic 'Short option is required!'
	[[ "${short}" =~ '^-[a-z0-9]$' ]] || panic "Expected short option in format '-<single char>', got instead: '${short}'"
	long="$2"
	if [ -n "$long" ]; then
		[[ "${long}" =~ '^--[a-z0-9][a-z0-9_-]+$' ]] || panic "Expected long option in format '--<name>', got instead: '${long}'"
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
	click::_type["$name"]='option'
	click::_help["$name"]="$help"
	click::_short["$name"]="$short"
	click::_long["$name"]="$long"
	click::_default["$name"]="$default"
}

click::argument() {
	# Registers positional argument.
	# Params: <name> <help>
	# E.g.:   'filename' 'Name of the input file.'
	# All positionals must be consumed.
	name="$1"
	[ -z "$name" ] && panic 'Argument name is required!'
	# TODO: nargs
	click::_type["$name"]='argument'
	click::_help["$name"]="$help"
	click::_arg_pos["$name"]="${click::_positional_count}"
	click::_positional_count=$((click::_positional_count + 1))
}

# TODO groups like click.group() for subcommands

click::usage() {
	# Prints usage message.
	usage="$0"
	for name in "${!click::_type[@]}"; do
		if [ ${click::_type[$name]} == 'option' -o ${click::_type[$name]} == 'flag' ]; then
			usage="$usage [${click::_short[$name]}]"
		fi
	done
	for name in "${!click::_type[@]}"; do
		if [ ${click::_type[$name]} == 'argument' ]; then
			usage="$usage <$name>"
		fi
	done
	echo "Usage: $usage"
	if [ -n "${click::_help}" ]; then
		echo "${click::_help}"
	fi
	for name in "${!click::_type[@]}"; do
		if [ ${click::_type[$name]} == 'option' -o ${click::_type[$name]} == 'flag' ]; then
			echo "${click::_short[$name]}"
			if [ -n "${click::_long[$name]}" ]; then
				echo "${click::_long[$name]}"
			fi
		elif [ ${click::_type[$name]} == 'argument' ]; then
			echo "$name"
		fi
		echo "${click::_help[$name]}"
		if [ ${click::_type[$name]} == 'option' ]; then
			echo "Default is '${click::_default[$name]}'."
		elif [ ${click::_type[$name]} == 'flag' ]; then
			echo "Default is false."
		fi
	done
}

# Main associative array of collected CLI args.
# Access: ${click::args[arg_name]}
declare -A click::args

click::run() {
	# Parses CLI arguments, calls registered command.
	# Usage: <list of arguments>
	# Any set of arguments can be passed.
	# Pass "$@" from the main script for real CLI args.
	if [ "$(LC_ALL=C type -t "${click::_command}")" != 'function' ]; then
		panic "click::command does not point to an existing shell function: '${click::_command}'" >&2
	fi

	for name in "${!click::_type[@]}"; do
		click::args["$name"]="${click::_default[$name]}"
	done
	current_arg_pos=0
	while [ -n "$1"]; do
		arg="$1"
		matched=''
		if [ "$arg" == '-h' -o "$arg" == '--help' ]; then
			click::usage >&2
			exit 0
		fi
		if [[ "$arg" =~ '^-.+' ]]; then
			for name in "${!click::_type[@]}"; do
				if [ ${click::_type[$name]} == 'flag' ]; then
					if [ ${click::_short[$name]} == "$arg" ]; then
						click::args["$name"] = 'true'
						matched=true
						break
					elif [ ${click::_long[$name]} == "$arg" ]; then
						click::args["$name"] = 'true'
						matched=true
						break
					fi
				elif [ ${click::_type[$name]} == 'option' ]; then
					if [ ${click::_short[$name]} == "$arg" ]; then
						shift # TODO: check that next value is present and is a value, not an option key.
						click::args["$name"] = "$1"
						matched=true
						break
					elif [ ${click::_long[$name]} == "$arg" ]; then
						shift # TODO: check that next value is present and is a value, not an option key.
						click::args["$name"] = "$1"
						matched=true
						break
					fi
				fi
			done
		else
			for name in "${!click::_type[@]}"; do
				if [ ${click::_type[$name]} == 'argument' ]; then
					if [ ${click::_arg_pos[$name]} == "$current_arg_pos" ]; then
						click::args["$name"] = "$1"
						current_arg_pos=$((current_arg_pos + 1))
						matched=true
						break
					fi
				fi
			done
		fi
		if [ -n "$matched" ]; then
			echo "Unknown argument: $arg" >&2
			click::usage >&2
			exit 1
		fi
		shift
	done
	if [ $current_arg_pos -lt ${click::_positional_count} ]; then
		for name in "${!click::_type[@]}"; do
			if [ ${click::_type[$name]} == 'argument' ]; then
				if [ ${click::_arg_pos[$name]} == "$current_arg_pos" ]; then
					panic "Positional argument is expected: '$name'"
				fi
			fi
		done
	fi

	"${click::command}"
	exit $?
}
