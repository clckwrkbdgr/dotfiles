#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
. "$XDG_CONFIG_HOME/lib/path.bash"

TMPBINDIR="/tmp/bin.$$"

setUp() {
	mkdir -p "$TMPBINDIR"
}

tearDown() {
	rm -rf "$TMPBINDIR"
}

should_strip_directory_from_PATH() {
	PATH="$XDG_CONFIG_HOME/bin:$TMPBINDIR:/usr/bin:/bin"
	assertStringsEqual "$PATH" "$XDG_CONFIG_HOME/bin:$TMPBINDIR:/usr/bin:/bin"
	path::strip "$TMPBINDIR"
	assertStringsEqual "$PATH" "$XDG_CONFIG_HOME/bin:/usr/bin:/bin"
}

should_strip_current_directory_from_PATH() {
	cd "$TMPBINDIR"
	PATH="$XDG_CONFIG_HOME/bin:$TMPBINDIR:/usr/bin:/bin"
	tmpscript="$(mktemp)"
	finally "rm -f '$tmpscript'"
	chmod +x "$tmpscript"
	cat >"$tmpscript" <<EOF
#!/bin/bash
. "$XDG_CONFIG_HOME/lib/path.bash"
path::strip_current
echo "\$PATH"
EOF
	assertOutputEqual "$tmpscript" "$XDG_CONFIG_HOME/bin:/usr/bin:/bin"
}

should_exec_base_app_from_wrapper() {
	PATH="$TMPBINDIR:$XDG_CONFIG_HOME/bin:/usr/bin:/bin"
	tmpscript="$TMPBINDIR/cat"
	cat >"$tmpscript" <<EOF
#!/bin/bash
. "\$XDG_CONFIG_HOME/lib/path.bash"
path::exec_base -vet "\$@"
EOF
	chmod +x "$tmpscript"
	assertOutputEqual 'which cat' "$TMPBINDIR/cat"
	assertOutputEqual "echo -e '\tTEST' | PATH='$TMPBINDIR:$XDG_CONFIG_HOME/bin:/usr/bin:/bin' cat" "^ITEST$"
}

unittest::run should_
