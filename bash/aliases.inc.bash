# User specific aliases.
alias rm='rm -i'
alias mv='mv -i'
alias cp='cp -i'
if [ `uname` == AIX ]; then
	alias ls='ls -F'
else
	alias ls='ls --color=auto -F'
fi
alias shuffle='find . -type f | sort -R | tail'
alias s='search.sh'
alias isodate='date +%Y-%m-%dT%H:%M:%S'
alias ranger-ctime='ranger --cmd="set sort ctime" --cmd="set sort_reverse true"'
alias .rogue='python ~/.config/.rogue/rogue.py'
alias qiv='qiv -f -t -i'
if [ `uname` != AIX ]; then
	alias grep='grep --color=auto'
fi
which vimdiff >/dev/null 2>&1 || alias vimdiff='vim -d'
alias zathura='zathura --mode=fullscreen'

function cdfind() {
	D="$(dirname "$(find . -name "$@" | tee /dev/stderr | head -1)")"
	[ -n "$D" ] && cd "$D"
}
export -f cdfind

if ! which tree >/dev/null 2>&1; then
	function tree() {
		find "${@:-.}" | sed -e 'sI/$II; sI[^/]*/I|- Ig; sI- |I  |Ig'
	}
	export -f tree
else
	alias tree='tree --charset=ascii'
fi

if ! which dos2unix >/dev/null 2>&1; then
	function dos2unix() {
		tmp="/tmp/tmp-dos2unix-$RANDOM.tmp"
		sed 's/$//g' <"$1" >"$tmp"
		mv -f "$tmp" "$1"
		rm -f "$tmp"
	}
	export -f dos2unix
fi

if ! which realpath >/dev/null 2>&1; then
	function realpath() {
		echo "$(cd "$(dirname "$1")"; pwd -P)/$(basename "$1")"
	}
	export -f realpath
fi
