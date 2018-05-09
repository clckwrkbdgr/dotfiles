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
	tput setf 4 # red
	filterconf -f "$format" $restore <"test.$format" | diff "expected.txt" - | cat -vet
	rc=$?
	tput sgr0
	rm -f "test.$format"
	return "$rc"
}

perform_test 'txt' 'smudge' should_smudge_home_dir_in_plain_text
perform_test 'txt' 'restore' should_restore_home_dir_in_plain_text

popd >/dev/null
rm -rf "$testdir"
