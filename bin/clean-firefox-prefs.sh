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
sed '/browser.shell.mostRecentDateSetAsDefault/d' | \
sed '/browser.slowStartup.averageTime/d' | \
sed '/browser.slowStartup.samples/d' | \
sed '/extensions.blocklist.pingCount.*/d' | \
sed '/extensions.getAddons.cache.lastUpdate/d' | \
sed '/idle.lastDailyNotification/d' | \
sed '/toolkit.startup.last_success/d' | \
sed '/storage.vacuum.last.places.sqlite/d' | \
sed '/storage.vacuum.last.index/d' | \
sed '/places.database.lastMaintenance/d' | \
sed '/extensions.@vkmad.sdk.load.reason/d' | \
sed '/extensions.firebug.defaultPanelName/d' | \
sed '/extensions.firebug.previousPlacement/d' | \
sed '/extensions.greasemonkey.newscript_namespace/d' | \
sed '/places.history.expiration.transient_current_max_pages/d' | \
sed '/extensions.ui.lastCategory/d' | \
sed '/font.internaluseonly.changed/d' | \
sed '/browser.sessionstore.upgradeBackup.latestBuildID/d' | \
sed '/browser.startup.homepage_override.buildID/d' | \
sed '/gecko.buildID/d' | \
sed '/media.gmp-manager.buildID/d' | \
sed '/gfx.crash-guard.glcontext.appVersion/d' | \
sed '/extensions\..*\.currentVersion/d' | \
sed '/extensions\.last[^.]*Version/d' | \
sed '/noscript.version/d' | \
sed '/noscript.ABE.cspHeaderDelim/d' | \
sed '/extensions.classicthemerestorer.pref_actindx/d' | \
sed '/extensions.classicthemerestorer.aboutprefs/d' | \
sed '/devtools.telemetry.tools.opened.version/d' | \
sed '/devtools.toolbox.selectedTool/d' | \
sed '/browser.uiCustomization.state/d' | \
sed '/browser.syncPromoViewsLeftMap/d' | \
sed '/devtools.webconsole.filter./d' | \
sed '/\(gecko\|browser\).*\.mstone/d' | \
sed '/extensions.[^.]\+.sdk.version/d' | \
sed 's/\(browser.uiCustomization.state.*newElementCount[^:]*\): *[0-9]\+/\1:1/' | \
sed '/extensions.greasemonkey.version/d' | \
sed '/extensions.browsec.tracking_cid/d' | \
sed 's/\(devtools.toolsidebar-width.webconsole\)", *[0-9]\+/\1", 300/' | \
sed '/devtools.toolbox.splitconsoleHeight/d' | \
sed '/devtools.debugger.ui.panes-[a-z]*-width/d' | \
sed '/devtools.toolbox.footer.height/d' | \
sed '/extensions.firefox@zenmate.com.sdk.version/d' | \
sed 's|'"$HOME"'|$HOME|g'
