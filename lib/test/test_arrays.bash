#!/bin/bash
. "$XDG_CONFIG_HOME/lib/arrays.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

should_print_usage_info() {
   declare -a indexed_array
   arrays::append indexed_array 1
   arrays::append indexed_array foo
   assertStringsEqual "${indexed_array[0]}" 1
   assertStringsEqual "${indexed_array[1]}" foo
}

unittest::run should_
