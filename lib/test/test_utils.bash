#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
. "$XDG_CONFIG_HOME/lib/utils.bash"

should_panic() {
	assertOutputEqual 'panic "ERROR" 2>&1; echo "this should not happen"' 'ERROR'
	assertExitFailure
}

should_check_if_string_starts_with_prefix() {
	assertExitSuccess 'startswith "foo bar" "foo b"'
	assertExitSuccess 'startswith "foo bar" "foo bar"'
	assertExitSuccess 'startswith "foo bar" ""'
	assertExitSuccess 'startswith "" ""'
	assertExitFailure 'startswith "foo bar" "foo bA"'
}

should_trim_whitespaces() {
	assertStringsEqual "$(trim "foo")" 'foo'
	assertStringsEqual "$(trim "foo  ")" 'foo'
	assertStringsEqual "$(trim "  foo")" 'foo'
	assertStringsEqual "$(trim "  foo  ")" 'foo'
	assertStringsEqual "$(trim "  with  spaces  ")" 'with  spaces'
}

should_perform_actions_finally() {
	assertOutputEqual "( finally 'echo finally'; echo 'test' )" "test\nfinally"
}

should_accumulate_finally_statements() {
	assertOutputEqual "( finally 'echo first finally'; echo 'test'; finally 'echo second finally';  )" "test\nfirst finally\nsecond finally"
}

should_perform_finally_in_separate_subshells_independently() {
	assertOutputEqual "( finally 'echo first'; echo 'test' )" "test\nfirst"
	assertOutputEqual "( finally 'echo second'; echo 'test' )" "test\nsecond"
}

should_warn_about_deprecated_function() {
	deprecated_function() {
		deprecated "Place your text here"
	}
	assertOutputEqual 'deprecated_function 2>&1' "$0:$(($LINENO-2)):function deprecated_function is deprecated: Place your text here"
}

should_warn_about_deprecated_script() {
	local tmpscript=$(mktemp)
	finally "rm -f '$tmpscript'"
	cat >"$tmpscript" <<EOF
. "$XDG_CONFIG_HOME/lib/utils.bash"
deprecated 'This whole script.'
EOF
	assertOutputEqual "bash $tmpscript 2>&1" "$tmpscript:2:script is deprecated: This whole script."
}

should_warn_about_deprecated_source_file() {
	local tmpscript=$(mktemp)
	local tmpsource=$(mktemp)
	finally "rm -f '$tmpscript' '$tmpsource' "
	cat >"$tmpsource" <<EOF
. "$XDG_CONFIG_HOME/lib/utils.bash"
deprecated 'This whole sourced file.'
EOF
	cat >"$tmpscript" <<EOF
. "$tmpsource"
EOF
	assertOutputEqual "bash $tmpscript 2>&1" "$tmpsource:2:script is deprecated: This whole sourced file."
}

should_detect_sourced_file() {
	local tmpsource=$(mktemp)
	finally "rm -f '$tmpsource'"
	cat >"$tmpsource" <<EOF
. "$XDG_CONFIG_HOME/lib/utils.bash"
is_sourced && IS_SOURCED=true
EOF
	local tmpscript=$(mktemp)
	finally "rm -f '$tmpscript'"
	cat >"$tmpscript" <<EOF
#!/bin/bash
. "$tmpsource"
[ -n "\$IS_SOURCED" ]
EOF
	chmod +x "$tmpscript"
	assertExitSuccess "bash $tmpscript"
}

should_detect_sourced_file_from_nested_function() {
	local tmpbase=$(mktemp)
	finally "rm -f '$tmpbase'"
	cat >"$tmpbase" <<EOF
. "$XDG_CONFIG_HOME/lib/utils.bash"
top_function() {
	is_sourced \$BASH_SOURCE
}
EOF
	local tmpsource=$(mktemp)
	finally "rm -f '$tmpsource'"
	cat >"$tmpsource" <<EOF
. "$tmpbase"
top_function && IS_SOURCED=true
EOF
	local tmpscript=$(mktemp)
	finally "rm -f '$tmpscript'"
	cat >"$tmpscript" <<EOF
#!/bin/bash
. "$tmpsource"
[ -n "\$IS_SOURCED" ]
EOF
	chmod +x "$tmpscript"
	assertExitSuccess "bash $tmpscript"
}

should_detect_main_script_file() {
	local tmpscript=$(mktemp)
	finally "rm -f '$tmpscript'"
	cat >"$tmpscript" <<EOF
#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
is_sourced
EOF
	chmod +x "$tmpscript"
	assertExitFailure "bash $tmpscript"
}

unittest::run should_
