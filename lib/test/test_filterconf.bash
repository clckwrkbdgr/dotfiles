#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"

should_smudge_home_dir_in_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "First: ${HOME}\nSecond: ${HOME}" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' enviro <'$test_file'" - <<EOF
First: \$HOME
Second: \$HOME
EOF
}

should_restore_home_dir_in_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e 'First: $HOME\nSecond: $HOME' >"$test_file"
	assertOutputEqual "filterconf -f 'txt' restore <'$test_file'" - <<EOF
First: ${HOME}
Second: ${HOME}
EOF
}

should_smudge_custom_env_var() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	XHOME="$LOGNAME"
	echo -e "First: ${XHOME}\nSecond: ${XHOME}" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' -e 'XHOME=echo \$LOGNAME' enviro <'$test_file'" - <<EOF
First: \$XHOME
Second: \$XHOME
EOF
}

should_restore_custom_env_var() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	XHOME="$LOGNAME"
	echo -e 'First: $XHOME\nSecond: $XHOME' >"$test_file"
	assertOutputEqual "filterconf -f 'txt' -e 'XHOME=echo \$LOGNAME' restore <'$test_file'" - <<EOF
First: ${XHOME}
Second: ${XHOME}
EOF
}

should_smudge_several_custom_env_vars() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	export XHOME="xhome"
	echo -e "First: ${XHOME}\nSecond: ${USER}" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' -e 'XHOME=\$XHOME' -e 'USERNAME=\$USER' enviro <'$test_file'" - <<EOF
First: \$XHOME
Second: \$USERNAME
EOF
}

should_restore_several_custom_env_vars() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	XHOME=$HOME
	echo -e 'First: $XHOME\nSecond: $USERNAME' >"$test_file"
	assertOutputEqual "filterconf -f 'txt' -e 'XHOME=echo \$HOME' -e 'USERNAME=\$USER' restore <'$test_file'" - <<EOF
First: ${XHOME}
Second: ${USER}
EOF
}

should_sort_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "b\nc\na" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' sort <'$test_file'" - <<EOF
a
b
c
EOF
}

should_delete_value_from_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "a\nb\nc" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' delete 'b' <'$test_file'" - <<EOF
a
c
EOF
}

should_delete_multiple_values_from_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "a\nb\nc" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' delete 'b' 'c' <'$test_file'" - <<EOF
a
EOF
}

should_delete_line_with_substring_from_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "first\nsecond\nthird" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' delete 'eco' <'$test_file'" - <<EOF
first
third
EOF
}

should_delete_regex_from_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "first\nsecond\nthird" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' delete '^se.on+d$' --pattern-type 'regex' <'$test_file'" - <<EOF
first
third
EOF
}

should_replace_substring_in_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "first\nsecond\nthird" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' replace 'seco' --with '2' <'$test_file'" - <<EOF
first
2nd
third
EOF
}

should_replace_regex_in_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "first\nsecond\nthird" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' replace '^seco([a-z]+)$' --pattern-type 'regex' --with '2\1' <'$test_file'" - <<EOF
first
2nd
third
EOF
}

should_prettify_plain_text() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	echo -e "first\n  second\n\tthird" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' pretty <'$test_file'" - <<EOF
first
  second
	third
EOF
}

should_perform_multiple_commands() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	local script_sh=$(mktemp)
	finally "rm -f '$script_sh'"
	cat >"$script_sh" <<EOF
# Comment
delete --pattern-type regex "^.*remove"
sort
replace --pattern-type regex "seco(nd)" --with "2\1"
EOF
	chmod +x "$script_sh"

	echo -e "second\nthird\nto remove\nfirst" >"$test_file"
	assertOutputEqual "filterconf -f 'txt' script '$script_sh' <'$test_file'" - <<EOF
first
2nd
third
EOF
}

unittest::run should_
