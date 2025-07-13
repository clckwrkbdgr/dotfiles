#/bin/bash

export_dbus() {
	# Export environment variables via DBUS for XFCE4 or Gnome.
	user=$(whoami)
	pid="$(pgrep -u $user xfce4-session) $(pgrep -u $user gnome-panel)"
	for dbusenv in $pid; do
		DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$dbusenv/environ | tr -d '\000' | sed -e 's/DBUS_SESSION_BUS_ADDRESS=//')
		data="DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"
		eval " export $data"
	done
}

current_desktop_environment() {
	# Detects current Desktop Environment.
	# Returns string ID. Known DEs are:
	# - xfce4
	# - ...and that's all. Otherwise returns 'gnome'
	if pgrep xfce4-panel >/dev/null; then
		echo 'xfce4'
	else
		echo 'gnome'
	fi
}

set_wallpaper() {
	# Sets wallpaper for current DE (detected automatically).
	$(current_desktop_environment)::set_wallpaper "$@"
}

get_wallpaper() {
	# Prints current wallpaper for current DE (detected automatically).
	$(current_desktop_environment)::get_wallpaper "$@"
}

get_monitor_name() {
	xrandr --query | grep '\bconnected\b' | awk '{print $1}'
}
_monitor_name=$(get_monitor_name)

xfce4::get_wallpaper() {
	xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor${_monitor_name}/workspace0/last-image
}

xfce4::set_wallpaper() {
	# Sets wallpaper for XFCE DE.
	wallpfile="$1"
	xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor${_monitor_name}/workspace0/last-image -s "$wallpfile" --create -t string
	xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor${_monitor_name}/workspace0/image-style -s 4 # Scaled
}

gnome::set_wallpaper() {
	# Sets wallpaper for Gnome DE (2 or 3?).
	wallpfile="$1"
	gconftool-2 -t string -s /desktop/gnome/background/picture_filename "$wallpfile"
	gsettings set org.gnome.desktop.background picture-uri "file://$wallpfile"
}

if [ "$1" == 'start-main-quake-terminal' ]; then
	background_tile=~/.config/images/quake-tile.png
	cd ~
	export FIX_SHLVL=$SHLVL
	exec urxvt  +tr -pixmap "$background_tile;0x0-100-100:op=tile"
fi
