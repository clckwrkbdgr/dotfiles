arrays::append() {
   # Wrapper to add value to array considering different versions of Bash.
   # Params: <array_name> <value>
   array_name=$1
   value=$2
   case "$BASH_VERSION" in
      3.*)
         eval "${array_name}[\${#${array_name}[@]}]=\"${value}\""
         ;;
      *)
         eval "${array_name}+=(\"${value}\")"
         ;;
   esac
}
