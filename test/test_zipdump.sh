#!/bin/bash

### DATA

function lorem_ipsum() {
cat <<EOF
Lorem ipsum
Dolores sit amet
EOF
}

### TESTS

function should_zip_simple_text_file() {
lorem_ipsum >'test.txt'
echo $(cat 'test.txt' | wc -c)'||test.txt'
cat 'test.txt'
echo # Content separator.

zip "test.zip" "test.txt" >&2
}

### MAIN

testdir=$(mktemp -d)
pushd "$testdir" >/dev/null

should_zip_simple_text_file >"expected.txt"
tput setf 4 # red
zipdump dump "test.zip" | diff "expected.txt" - | cat -vet
tput sgr0

popd >/dev/null
rm -rf "$testdir"
