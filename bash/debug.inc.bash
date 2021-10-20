_clckwrkbdgr_debug_profile() {
   [ -n "$CLCKWRKBDGR_DEBUG_PROFILE" ] && echo `date +"%T.%N:"` "${BASH_SOURCE[1]}:" "$@" >&2
}
