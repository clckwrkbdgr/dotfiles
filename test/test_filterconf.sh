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

### MAIN

testdir=$(mktemp -d)
pushd "$testdir" >/dev/null

function perform_test() { # <format> <smudge|restore> <test name>
	format="$1"
	if [ "$2" == "smudge" ]; then
		restore=""
	elif [ "$2" == "restore" ]; then
		restore="--restore"
	else
		echo "Expected smudge/restore, got: $2"
		return 1
	fi
	echo ">>> $3"
	"$3" >"expected.txt"
	shift 3 # Make rooms for custom args.
	tput setf 4 # red
	export LANGUAGE=en_US:en # To make `diff` output 'printable'.
	filterconf -f "$format" $restore "$@" <"test.$format" | diff "expected.txt" - | cat -vet
	rc=$?
	tput sgr0
	rm -f "test.$format"
	return "$rc"
}

perform_test 'txt' 'smudge' should_smudge_home_dir_in_plain_text
perform_test 'txt' 'restore' should_restore_home_dir_in_plain_text
perform_test 'txt' 'smudge' should_smudge_custom_env_var -e 'XHOME=echo $HOME'
perform_test 'txt' 'restore' should_restore_custom_env_var -e 'XHOME=echo $HOME'
perform_test 'txt' 'smudge' should_smudge_several_custom_env_vars -e 'XHOME=echo $HOME' -e 'USERNAME=$USER'
perform_test 'txt' 'restore' should_restore_several_custom_env_vars -e 'XHOME=echo $HOME' -e 'USERNAME=$USER'

perform_test 'txt' 'smudge' should_sort_plain_text --sort
perform_test 'txt' 'smudge' should_delete_value_from_plain_text --delete 'b'

popd >/dev/null
rm -rf "$testdir"
