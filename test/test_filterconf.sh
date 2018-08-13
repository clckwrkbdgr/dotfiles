#!/bin/bash

function assert_files_equal() { # <file_actual> <file_expected>
	actual="$1"
	expected="$2"
	tput setf 4 # red
	export LANGUAGE=en_US:en # To make `diff` output 'printable'.
	diff "$expected" "$actual" | cat -vet
	rc=$?
	tput sgr0
	return "$rc"
}

### TESTS

function should_smudge_home_dir_in_plain_text() {
	echo -e 'First: $HOME\nSecond: $HOME' >expected.txt
	echo -e "First: ${HOME}\nSecond: ${HOME}" >test.txt
	filterconf -f 'txt' enviro <test.txt >actual.txt
}

function should_restore_home_dir_in_plain_text() {
	echo -e "First: ${HOME}\nSecond: ${HOME}" >expected.txt
	echo -e 'First: $HOME\nSecond: $HOME' >test.txt
	filterconf -f 'txt' restore <test.txt >actual.txt
}

function should_smudge_custom_env_var() {
	echo -e 'First: $XHOME\nSecond: $XHOME' >expected.txt
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${XHOME}" >test.txt
	filterconf -f 'txt' -e 'XHOME=echo $HOME' enviro <test.txt >actual.txt
}

function should_restore_custom_env_var() {
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${XHOME}" >expected.txt
	echo -e 'First: $XHOME\nSecond: $XHOME' >test.txt
	filterconf -f 'txt' -e 'XHOME=echo $HOME' restore <test.txt >actual.txt
}

function should_smudge_several_custom_env_vars() {
	echo -e 'First: $XHOME\nSecond: $USERNAME' >expected.txt
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${USER}" >test.txt
	filterconf -f 'txt' -e 'XHOME=echo $HOME' -e 'USERNAME=$USER' enviro <test.txt >actual.txt
}

function should_restore_several_custom_env_vars() {
	XHOME=$HOME
	echo -e "First: ${XHOME}\nSecond: ${USER}" >expected.txt
	echo -e 'First: $XHOME\nSecond: $USERNAME' >test.txt
	filterconf -f 'txt' -e 'XHOME=echo $HOME' -e 'USERNAME=$USER' restore <test.txt >actual.txt
}

function should_sort_plain_text() {
	echo -e 'a\nb\nc' >expected.txt
	echo -e "b\nc\na" >test.txt
	filterconf -f 'txt' sort <test.txt >actual.txt
}

function should_delete_value_from_plain_text() {
	echo -e 'a\nc' >expected.txt
	echo -e "a\nb\nc" >test.txt
	filterconf -f 'txt' delete 'b' <test.txt >actual.txt
}

function should_delete_multiple_values_from_plain_text() {
	echo -e 'a' >expected.txt
	echo -e "a\nb\nc" >test.txt
	filterconf -f 'txt' delete 'b' 'c' <test.txt >actual.txt
}

function should_delete_line_with_substring_from_plain_text() {
	echo -e 'first\nthird' >expected.txt
	echo -e "first\nsecond\nthird" >test.txt
	filterconf -f 'txt' delete 'eco' <test.txt >actual.txt
}

function should_delete_regex_from_plain_text() {
	echo -e 'first\nthird' >expected.txt
	echo -e "first\nsecond\nthird" >test.txt
	filterconf -f 'txt' delete '^se.on+d$' --pattern-type 'regex' <test.txt >actual.txt
}

function should_replace_substring_in_plain_text() {
	echo -e 'first\n2nd\nthird' >expected.txt
	echo -e "first\nsecond\nthird" >test.txt
	filterconf -f 'txt' replace 'seco' --with '2' <test.txt >actual.txt
}

function should_replace_regex_in_plain_text() {
	echo -e 'first\n2nd\nthird' >expected.txt
	echo -e "first\nsecond\nthird" >test.txt
	filterconf -f 'txt' replace '^seco([a-z]+)$' --pattern-type 'regex' --with '2\1' <test.txt >actual.txt
}

function should_prettify_plain_text() {
	echo -e 'first\n  second\n\tthird' >expected.txt
	echo -e "first\n  second\n\tthird" >test.txt
	filterconf -f 'txt' pretty <test.txt >actual.txt
}

function should_perform_multiple_commands() {
	echo '# Comment' >script.sh
	echo 'delete --pattern-type regex "^.*remove"' >>script.sh
	echo 'sort' >>script.sh
	echo 'replace --pattern-type regex "seco(nd)" --with "2\1"' >>script.sh

	echo -e 'first\n2nd\nthird' >expected.txt
	echo -e "second\nthird\nto remove\nfirst" >test.txt
	filterconf -f 'txt' script 'script.sh' <test.txt >actual.txt
}

### MAIN


function perform_test() { # <format> <smudge|restore> <test name>
	testdir=$(mktemp -d -p $XDG_RUNTIME_DIR)
	pushd "$testdir" >/dev/null

	echo ">>> $1"
	"$1"
	assert_files_equal "actual.txt" "expected.txt"
	rc=$?

	popd >/dev/null
	rm -rf "$testdir"

	return "$rc"
}

perform_test should_smudge_home_dir_in_plain_text
perform_test should_restore_home_dir_in_plain_text
perform_test should_smudge_custom_env_var
perform_test should_restore_custom_env_var
perform_test should_smudge_several_custom_env_vars
perform_test should_restore_several_custom_env_vars

perform_test should_sort_plain_text
perform_test should_delete_value_from_plain_text
perform_test should_delete_multiple_values_from_plain_text
perform_test should_delete_line_with_substring_from_plain_text
perform_test should_delete_regex_from_plain_text
perform_test should_replace_substring_in_plain_text
perform_test should_replace_regex_in_plain_text
perform_test should_prettify_plain_text

perform_test should_perform_multiple_commands

