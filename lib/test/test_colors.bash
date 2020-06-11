#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
. "$XDG_CONFIG_HOME/lib/colors.bash"

setUp() {
	color::init on
}

tearDown() {
	color::init auto
	color::reset
}

should_use_colors_in_strings() {
	assertStringsEqual "${red}the red in the sky is ours${reset_color}" \
		'\033[0;31mthe red in the sky is ours\033[0m'
}

should_reset_previously_instated_color_mode() {
	paint_it_red() {
		echo -e "${red}Vision red..."
		color::reset
		echo -e "No more color, no more light."
	}
	assertOutputEqual paint_it_red "${red}Vision red...\n${reset_color}No more color, no more light."
}

should_force_init_colors() {
	color::init off
	assertStringsEqual "${red}Not red${reset_color}" 'Not red'
	color::init on
	assertOutputEqual 'echo -e "${red}Not red${reset_color}" | cat' '\033[0;31mNot red\033[0m'
}

should_autodetect_tty_for_colors() {
	color::init off
	assertStringsEqual "${red}" ''
	color::init auto
	assertStringsEqual "${red}" '\033[0;31m'
	(
		color::init auto
		assertStringsEqual "${red}" ''
	) | cat
}

should_strip_color_sequences_from_string() {
	assertOutputEqual 'echo -e "${red}foo${blue}bar" | color::strip' 'foobar'
}

unittest::run should_
