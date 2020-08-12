# Main sourceable script to load XDG-compliant environment.
# Can be included in bashrc or profile.
. ~/.config/xdg/base.inc.sh
. ~/.config/xdg/config.inc.sh
. ~/.config/xdg/data.inc.sh
. ~/.config/xdg/state.inc.sh
. ~/.config/xdg/cache.inc.sh
. ~/.config/xdg/runtime.inc.sh
if [ -n "$BASH" ]; then
	. ~/.config/xdg/path.inc.sh
fi

. "$XDG_CONFIG_HOME/lib/utils.sh"
deprecated 'Source all ~/.config/xdg/*.sh files instead'
