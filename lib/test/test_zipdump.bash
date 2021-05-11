#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"

if [ $(uname) == AIX ]; then
   if which openssl >/dev/null 2>&1; then
      base64() {
         openssl base64
      }
   elif which python >/dev/null 2>&1; then
      base64() {
         python -m base64
      }
   fi
fi

should_zip_simple_text_file() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	cat >"$test_file" <<EOF
Lorem ipsum
Dolores sit amet
EOF
	local test_zip=$(mktemp --dry-run --suffix .zip)
	finally "rm -f '$test_zip'"
	local expected_file=$(mktemp)
	finally "rm -f '$expected_file'"

	local zip_content_test_file=${test_file#/}
	(
	echo $(cat "$test_file" | wc -c)"|utf-8|$zip_content_test_file"
	cat "$test_file"
	echo # Content separator.
	) >"$expected_file"

	zip "$test_zip" "$test_file" | grep -v '^  adding:' >&2

	cat "$expected_file" | assertOutputEqual "zipdump dump '$test_zip'" -
}

should_zip_utf8() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	cat >"$test_file" <<EOF
Лорем ипсум
Долорес сит амет
EOF
	local test_zip=$(mktemp --dry-run --suffix .zip)
	finally "rm -f '$test_zip'"
	local expected_file=$(mktemp)
	finally "rm -f '$expected_file'"

	local zip_content_test_file=${test_file#/}
	(
	echo $(cat "$test_file" | wc -c)"|utf-8|$zip_content_test_file"
	cat "$test_file"
	echo # Content separator.
	) >"$expected_file"

	zip "$test_zip" "$test_file" | grep -v '^  adding:' >&2

	cat "$expected_file" | assertOutputEqual "zipdump dump '$test_zip'" -
}

should_zip_cp1251() {
	local test_file=$(mktemp)
	finally "rm -f '$test_file'"
	cat <<EOF | iconv -f 'utf-8' -t 'cp1251' >"$test_file"
Лорем ипсум
Долорес сит амет
EOF
	local test_zip=$(mktemp --dry-run --suffix .zip)
	finally "rm -f '$test_zip'"
	local expected_file=$(mktemp)
	finally "rm -f '$expected_file'"

	local zip_content_test_file=${test_file#/}
	size=$(cat "$test_file" | base64 | wc -c)
	size=$((size-1))
	(
	echo "$size|base64|$zip_content_test_file"
	cat "$test_file" | base64 | tr -d '\n'
	echo # Content separator.
	) >"$expected_file"

	zip "$test_zip" "$test_file" | grep -v '^  adding:' >&2

	cat "$expected_file" | assertOutputEqual "zipdump dump '$test_zip'" -
}

unittest::run should_
