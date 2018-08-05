#!/bin/bash

### TESTS

function should_smudge_home_dir_in_plain_text() {
	echo -e 'First: $HOME\nSecond: $HOME' # Expected.
	echo -e "First: ${HOME}\nSecond: ${HOME}" >test.txt
}

function should_restore_home_dir_in_plain_text() {
	echo -e "First: ${HOME}\nSecond: ${HOME}" # Expected.
	echo -e 'First: $HOME\nSecond: $HOME' >test.txt
}

function should_smudge_custom_env_var() {
	echo -e 'First: $XHOME\nSecond: $XHOME' # Expected.
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${XHOME}" >test.txt
}

function should_restore_custom_env_var() {
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${XHOME}" # Expected.
	echo -e 'First: $XHOME\nSecond: $XHOME' >test.txt
}

function should_smudge_several_custom_env_vars() {
	echo -e 'First: $XHOME\nSecond: $USERNAME' # Expected.
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${USER}" >test.txt
}

function should_restore_several_custom_env_vars() {
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${USER}" # Expected.
	echo -e 'First: $XHOME\nSecond: $USERNAME' >test.txt
}

function should_sort_plain_text() {
	echo -e 'a\nb\nc' # Expected.
	echo -e "b\nc\na" >test.txt
}

function should_delete_value_from_plain_text() {
	echo -e 'a\nc' # Expected.
	echo -e "a\nb\nc" >test.txt
}

function should_delete_multiple_values_from_plain_text() {
	echo -e 'a' # Expected.
	echo -e "a\nb\nc" >test.txt
}

function should_delete_line_with_substring_from_plain_text() {
	echo -e 'first\nthird' # Expected.
	echo -e "first\nsecond\nthird" >test.txt
}

function should_delete_regex_from_plain_text() {
	echo -e 'first\nthird' # Expected.
	echo -e "first\nsecond\nthird" >test.txt
}

function should_replace_substring_in_plain_text() {
	echo -e 'first\n2nd\nthird' # Expected.
	echo -e "first\nsecond\nthird" >test.txt
}

function should_replace_regex_in_plain_text() {
	echo -e 'first\n2nd\nthird' # Expected.
	echo -e "first\nsecond\nthird" >test.txt
}

function should_prettify_plain_text() {
	echo -e 'first\n  second\n\tthird' # Expected.
	echo -e "first\n  second\n\tthird" >test.txt
}

function should_perform_multiple_commands() {
	echo '# Comment' >script.sh
	echo 'delete --pattern-type regex "^.*remove"' >>script.sh
	echo 'sort' >>script.sh
	echo 'replace --pattern-type regex "seco(nd)" --with "2\1"' >>script.sh

	echo -e 'first\n2nd\nthird' # Expected.
	echo -e "second\nthird\nto remove\nfirst" >test.txt
}

### MAIN

testdir=$(mktemp -d)
pushd "$testdir" >/dev/null

function perform_test() { # <format> <smudge|restore> <test name>
	format="$1"
	echo ">>> $2"
	"$2" >"expected.txt"
	shift 2 # Make rooms for custom args.
	tput setf 4 # red
	export LANGUAGE=en_US:en # To make `diff` output 'printable'.
	filterconf -f "$format" "$@" <"test.$format" | diff "expected.txt" - | cat -vet
	rc=$?
	tput sgr0
	rm -f "test.$format"
	return "$rc"
}

perform_test 'txt' should_smudge_home_dir_in_plain_text enviro
perform_test 'txt' should_restore_home_dir_in_plain_text restore
perform_test 'txt' should_smudge_custom_env_var -e 'XHOME=echo $HOME' enviro
perform_test 'txt' should_restore_custom_env_var -e 'XHOME=echo $HOME' restore
perform_test 'txt' should_smudge_several_custom_env_vars -e 'XHOME=echo $HOME' -e 'USERNAME=$USER' enviro
perform_test 'txt' should_restore_several_custom_env_vars -e 'XHOME=echo $HOME' -e 'USERNAME=$USER' restore

perform_test 'txt' should_sort_plain_text sort
perform_test 'txt' should_delete_value_from_plain_text delete 'b'
perform_test 'txt' should_delete_multiple_values_from_plain_text delete 'b' 'c'
perform_test 'txt' should_delete_line_with_substring_from_plain_text delete 'eco'
perform_test 'txt' should_delete_regex_from_plain_text delete '^se.on+d$' --pattern-type 'regex'
perform_test 'txt' should_replace_substring_in_plain_text replace 'seco' --with '2'
perform_test 'txt' should_replace_regex_in_plain_text replace '^seco([a-z]+)$' --pattern-type 'regex' --with '2\1'
perform_test 'txt' should_prettify_plain_text pretty

perform_test 'txt' should_perform_multiple_commands script 'script.sh'

popd >/dev/null
rm -rf "$testdir"
