if [ $(uname) == Linux ]; then
	_gnu_sed=true
fi

color::init() {
	# Inits color mode.
	# By default colors are on for TTY shells, and off for non-TTY.
	# Call this function explicit args to force color mode on or off:
	#   color::init [auto]
	#   color::init on
	#   color::init off

	# TODO click
	local color_mode="${1:-auto}"
	if [ "$color_mode" == 'auto' ]; then
		if [ -t 1 ]; then
			color_mode='on'
		else
			color_mode='off'
		fi
	fi

	if [ "$color_mode" == 'on' ]; then
      black='\033[0;30m'
        red='\033[0;31m'
      green='\033[0;32m'
     yellow='\033[0;33m'
       blue='\033[0;34m'
     purple='\033[0;35m'
       cyan='\033[0;36m'
      white='\033[0;37m'
 bold_black='\033[1;30m'
   bold_red='\033[1;31m'
 bold_green='\033[1;32m'
bold_yellow='\033[1;33m'
  bold_blue='\033[1;34m'
bold_purple='\033[1;35m'
  bold_cyan='\033[1;36m'
 bold_white='\033[1;37m'
reset_color='\033[0m'
	elif [ "$color_mode" == 'off' ]; then
      black=''
        red=''
      green=''
     yellow=''
       blue=''
     purple=''
       cyan=''
      white=''
 bold_black=''
   bold_red=''
 bold_green=''
bold_yellow=''
  bold_blue=''
bold_purple=''
  bold_cyan=''
 bold_white=''
reset_color=''
	else
		echo "Unknown mode for color::init: <$color_mode>" >&2
	fi
}

color::reset() {
	# Resets both stdout and stderr color modes if there were any.
	echo -en "${reset_color}"
	echo -en "${reset_color}" >&2
}

color::strip() {
	# Strips stdin from coloring escape sequences, returning only text.
	if [ -n "${_gnu_sed}" ]; then
		sed "s%\x1b"'\(\[[0-9]\+\(;[0-9]\+\)\?m\|\][0-9]\+;\)%%g;s%\\\[\\\]%%g';
	else
		perl -pe "s%\e"'(\[[0-9]+(;[0-9]+)?m|\][0-9]+;)%%g;s%\\\[\\\]%%g'
	fi
}

color::init auto
