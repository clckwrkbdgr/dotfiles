arrays::append() {
   # Wrapper to add value to array considering different versions of Bash.
   # Params: <array_name> <value>
   local array_name=$1
   local value=$2
   case "$BASH_VERSION" in
      3.*)
         eval "${array_name}[\${#${array_name}[@]}]=\"${value}\""
         ;;
      *)
         eval "${array_name}+=(\"${value}\")"
         ;;
   esac
}

arrays::declare_assoc() {
   # Declares associative array considering different versions of Bash.
   # NOTE: Should be executed via eval:
   #       eval "$(arrays::declare_assoc <args...>)"
   # Params: <array_name> [<separator>]
   #
   # NOTE: Bash 3.* does not support associative arrays,
   #       so indexes arrays are used instead. Key is stored in the value itself,
   #       separated from the real value by <separator> string.
   #       Obviously arrays created using this function should be accessed by
   #       other functions (from this module) aware of this hack.
   #       Default separator is "|"
   local array_name=$1
   local separator=${2:-"|"}
   case "$BASH_VERSION" in
      3.*)
         echo "declare -a ${array_name}"
         echo "${array_name}_array_separator='${separator}'"
         ;;
      *)
         echo "declare -x -A ${array_name}"
         ;;
   esac
}

arrays::set_assoc() {
   # Sets value in associative array considering different versions of Bash.
   # Params: <array_name> <key> <value>
   local array_name="$1"
   local key="$2"
   local value="$3"
   case "$BASH_VERSION" in
      3.*)
         eval "local array_separator=\${${array_name}_array_separator}"
         eval 'for array_iter_index in "${!'"${array_name}"'[@]}"; do'\
            'local array_iter_value="${'"${array_name}"'[$array_iter_index]}";'\
            'case "$array_iter_value" in'\
               "'${key}${array_separator}'"'* ) '\
               "${array_name}"'[${array_iter_index}]='"'${key}${array_separator}${value}';"\
               'return 0 ;;'\
            'esac'\
         'done;'
         eval "${array_name}"'[${#'"${array_name}"'[@]}]='"'${key}${array_separator}${value}'"
         ;;
      *)
         eval "${array_name}[${key}]='${value}'"
         ;;
   esac
}

arrays::has_assoc() {
   # Returns zero if key is present in associative array
   # considering different versions of Bash.
   # Returns non-zero otherwise.
   # Params: <array_name> <key>
   local array_name="$1"
   local key="$2"
   case "$BASH_VERSION" in
      3.*)
         eval "local array_separator=\${${array_name}_array_separator}"
         eval 'for array_iter_value in "${'"${array_name}"'[@]}"; do'\
            'case "$array_iter_value" in'\
               "'${key}${array_separator}'"'* ) return 0 ;;'\
            'esac'\
         'done;'
         return 1
         ;;
      *)
         eval '[ -n "${'"${array_name}"'['"${key}"']+true}" ]'
         return $?
         ;;
   esac
}

arrays::get_assoc() {
   # Prints value from associative array considering different versions of Bash.
   # Params: <array_name> <key>
   local array_name="$1"
   local key="$2"
   case "$BASH_VERSION" in
      3.*)
         eval "local array_separator=\${${array_name}_array_separator}"
         eval 'for array_iter_value in "${'"${array_name}"'[@]}"; do'\
            'case "$array_iter_value" in'\
               "'${key}${array_separator}'"'* ) echo "${array_iter_value#*'"${array_separator}"'}"; break ;;'\
            'esac'\
         'done;'
         ;;
      *)
         eval 'echo ${'"${array_name}"'['"${key}"']}'
         ;;
   esac
}

arrays::list_assoc_keys() {
   # Lists keys from associative array considering different versions of Bash.
   # Fills another (linear) array with all the keys.
   # NOTE: It should be declared before calling this function!
   # Params: <array_name> <keys_array_name>
   local array_name="$1"
   local key_array_name="$2"
   case "$BASH_VERSION" in
      3.*)
         eval "local array_separator=\${${array_name}_array_separator}"
         eval 'for array_iter_value in "${'"${array_name}"'[@]}"; do'\
            "${key_array_name}[\${#${key_array_name}[@]}]="'"${array_iter_value%%'"${array_separator}"'*}";'\
         'done;'
         ;;
      *)
         eval 'for _name in "${!'"$array_name"'[@]}"; do '"arrays::append ${key_array_name}"' ${_name}; done'
         ;;
   esac
}
