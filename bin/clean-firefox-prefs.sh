#!/bin/sh
if [ "$1" = "--restore" ]; then
	sed 's|$HOME|'"$HOME"'|g'
	exit
fi
sed '/app[.]update[.]lastUpdateTime/d' | \
sed '/browser[.]safebrowsing[.]provider[.]mozilla[.][^.]*updatetime/d' | \
sed '/capability.policy.maonoscript.sites/d' | \
sed '/datareporting.sessions.previous/d' | \
sed '/devtools.scratchpad.recentFilePaths/d' | \
sed '/extensions.adblockplus.notificationdata/d' | \
sed '/extensions.bootstrappedAddons/d' | \
sed '/extensions.downloadyoutubemp4[.]/d' | \
sed '/extensions.enabled[^.]\+/d' | \
sed '/extensions.firefox@ghostery.com.sdk.rootURI/d' | \
sed '/extensions.sqlitemanager.jsonMruData/d' | \
sed '/extensions.xpiState/d' | \
sed '/noscript.subscription.lastCheck/d' | \
sed '/print.print_to_filename/d' | \
sed 's|'"$HOME"'|$HOME|g'
