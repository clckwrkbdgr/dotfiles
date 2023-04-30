#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
. "$XDG_CONFIG_HOME/lib/utils.bash"

if ! which realpath >/dev/null 2>&1; then
   function realpath() { # FIXME duplicated definition; first one is in .config/bash/aliases.inc.bash. Should move all those wrappers to some common file.
      echo "$(cd "$(dirname "$1")"; pwd -P)/$(basename "$1")"
   }
   export -f realpath
fi


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

should_check_if_string_ends_with_suffix() {
	assertExitSuccess 'endswith "foo bar" "oo bar"'
	assertExitSuccess 'endswith "foo bar" "foo bar"'
	assertExitSuccess 'endswith "foo bar" ""'
	assertExitSuccess 'endswith "" ""'
	assertExitFailure 'endswith "foo bar" "_bar"'
}

should_trim_whitespaces() {
	assertStringsEqual "$(trim "foo")" 'foo'
	assertStringsEqual "$(trim "foo  ")" 'foo'
	assertStringsEqual "$(trim "  foo")" 'foo'
	assertStringsEqual "$(trim "  foo  ")" 'foo'
	assertStringsEqual "$(trim "  with  spaces  ")" 'with  spaces'
}

should_find_item_in_array() {
	array=("foo"  "bar"  "value with spaces")
	assertExitSuccess 'item_in foo "${array[@]}"'
	assertExitSuccess 'item_in bar "${array[@]}"'
	assertExitFailure 'item_in MISSING "${array[@]}"'
	assertExitSuccess 'item_in "value with spaces" "${array[@]}"'
	assertExitFailure 'item_in "  foo" "${array[@]}"'
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
	local tmpbindir=$(mktemp -d)
	finally "rm -f '$tmpscript'; rm -rf '$tmpbindir'; "
	cat >"$tmpbindir/pstree" <<EOF
echo Mock pstree \$1 \$2 \$3
EOF
	chmod u+x "$tmpbindir/pstree"
	cat >"$tmpscript" <<EOF
. "$XDG_CONFIG_HOME/lib/utils.bash"
deprecated 'This whole script.'
EOF
	(
		export PATH="$tmpbindir:$PATH"
		assertOutputEqual "bash $tmpscript 2>&1" - <<EOF
$tmpscript:2:script is deprecated: This whole script.
Mock pstree -s -A -a
EOF
	)
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

should_convert_file_path_to_uri() {
	this_file="$(realpath "$0")"
	assertStringsEqual "$(as_uri "$this_file")" "file://$this_file"
}

should_truncate() {
	local tmplogfile=$(mktemp)
	finally "rm -f '$tmplogfile'"
	cat >"$tmplogfile" <<EOF
first
second
third
last
EOF
	truncate_logfile "$tmplogfile" 2
	assertOutputEqual "cat '$tmplogfile'" - <<EOF
third
last
EOF
}

should_compare_versions() {
	assertOutputEqual "version_cmp 1 2"         '<'
	assertOutputEqual "version_cmp 1.0.0 2.0.0" '<'
	assertOutputEqual "version_cmp 1.1.0 1.2.0" '<'
	assertOutputEqual "version_cmp 1.1 1.2.0"   '<'
	assertOutputEqual "version_cmp 1.1 1.1.0"   '<'

	assertOutputEqual "version_cmp '' ''"       '='
	assertOutputEqual "version_cmp 1 1."        '='
	assertOutputEqual "version_cmp 1.0.0 1.0.0" '='
	assertOutputEqual "version_cmp 0.0.0 0.0.0" '='

	assertOutputEqual "version_cmp 2.0.0 1.0.0" '>'
	assertOutputEqual "version_cmp 1.1.0 1.1"   '>'
}

unittest::run should_
