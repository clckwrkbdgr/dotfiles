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
