#!/bin/bash

### DATA

function lorem_ipsum() {
cat <<EOF
Lorem ipsum
Dolores sit amet
EOF
}

function ryba_utf8() {
cat <<EOF
Лорем ипсум
Долорес сит амет
EOF
}

### TESTS

function should_zip_simple_text_file() {
lorem_ipsum >'test.txt'
echo $(cat 'test.txt' | wc -c)'|utf-8|test.txt'
cat 'test.txt'
echo # Content separator.

zip "test.zip" "test.txt" >&2
}

function should_zip_utf8() {
ryba_utf8 >'test.txt'
echo $(cat 'test.txt' | wc -c)'|utf-8|test.txt'
cat 'test.txt'
echo # Content separator.

zip "test.zip" "test.txt" >&2
}

function should_zip_cp1251() {
ryba_utf8 | iconv -f 'utf-8' -t 'cp1251' >'test.txt'
size=$(cat 'test.txt' | base64 | wc -c)
size=$((size-1))
echo $size'|base64|test.txt'
cat 'test.txt' | base64 | tr -d '\n'
echo # Content separator.

zip "test.zip" "test.txt" >&2
}

### MAIN

testdir=$(mktemp -d)
pushd "$testdir" >/dev/null

function perform_test() { # <test name>
	echo ">>> $1"
	"$1" >"expected.txt"
	tput setf 4 # red
	zipdump dump "test.zip" | diff "expected.txt" - | cat -vet
	rc=$?
	tput sgr0
	rm -f "test.zip"
	return "$rc"
}

perform_test should_zip_simple_text_file
perform_test should_zip_utf8
perform_test should_zip_cp1251

popd >/dev/null
rm -rf "$testdir"
