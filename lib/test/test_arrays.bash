#!/bin/bash
. "../lib/arrays.bash"
. "../lib/unittest.bash"

should_append_values_to_array() {
   declare -a indexed_array
   arrays::append indexed_array 1
   arrays::append indexed_array foo
   assertStringsEqual "${indexed_array[0]}" 1
   assertStringsEqual "${indexed_array[1]}" foo
}

should_append_values_with_subshells_to_array() {
   declare -a indexed_array
   arrays::append indexed_array "foo$""(subshell)"
   assertStringsEqual "${indexed_array[0]}" "foo$""(subshell)"
}

unittest::run should_
