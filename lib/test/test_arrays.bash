#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/arrays.bash"

# TODO not using unittest.bash because it itself depends on correct work of arrays. So need another way to autodiscover-and-run this file.

declare -a indexed_array

arrays::append indexed_array 1
arrays::append indexed_array foo
[ ${indexed_array[0]} == 1 ] || panic "$0:FAIL: arrays::append"
[ ${indexed_array[1]} == foo ] || panic "$0:FAIL: arrays::append"

eval "$(arrays::declare_assoc assoc_array)"
arrays::set_assoc assoc_array second foo
arrays::set_assoc assoc_array first 1

arrays::has_assoc assoc_array first || panic "$0:FAIL: arrays::has_assoc first"
arrays::has_assoc assoc_array second || panic "$0:FAIL: arrays::has_assoc second"
arrays::has_assoc assoc_array unknown && panic "$0:FAIL: arrays::has_assoc unknown"

value=$(arrays::get_assoc assoc_array first)
[ "$value" == 1 ] || panic "$0:FAIL: arrays::get_assoc first: $value"

value=$(arrays::get_assoc assoc_array second)
[ "$value" == foo ] || panic "$0:FAIL: arrays::get_assoc second: $value"

arrays::set_assoc assoc_array second bar
value=$(arrays::get_assoc assoc_array second)
[ "$value" == bar ] || panic "$0:FAIL: arrays::set_assoc second second: $value"

declare -a all_keys
arrays::list_assoc_keys assoc_array all_keys
value=
for key in "${all_keys[@]}"; do
   value="${value}|$key"
done
[ "$value" == "|second|first" ] || panic "$0:FAIL: arrays::list_assoc_keys: $value"
