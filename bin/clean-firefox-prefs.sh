#!/bin/sh
if [ "$1" = "--restore" ]; then
	sed 's|$HOME|'"$HOME"'|g'
	exit
fi
sed '/app[.]update[.]lastUpdateTime/d' | \
sed '/browser[.]safebrowsing[.]provider[.]\(mozilla\|google\)[.][^.]*updatetime/d' | \
sed '/capability.policy.maonoscript.sites/d' | \
sed '/datareporting.sessions.previous/d' | \
sed '/datareporting.sessions.current/d' | \
sed '/datareporting.sessions.prunedIndex/d' | \
sed '/devtools.scratchpad.recentFilePaths/d' | \
sed '/devtools.telemetry.tools.opened.version/d' | \
sed '/devtools.webconsole.filter./d' | \
sed '/devtools.debugger.ui.panes-[a-z]*-width/d' | \
sed 's/\(devtools.toolsidebar-width.webconsole\)", *[0-9]\+/\1", 300/' | \
sed '/devtools.toolbox.splitconsoleHeight/d' | \
sed '/devtools.toolbox.splitconsoleEnabled/d' | \
sed '/devtools.toolbox.selectedTool/d' | \
sed '/devtools.toolbox.footer.height/d' | \
sed '/devtools.toolbox.previousHost/d' | \
sed '/devtools.toolbox.host/d' | \
sed '/devtools.netmonitor.filters/d' | \
sed '/devtools.netmonitor.panes-.*-width/d' | \
sed '/extensions.adblockplus.notificationdata/d' | \
sed '/extensions.bootstrappedAddons/d' | \
sed '/extensions.downloadyoutubemp4[.]/d' | \
sed '/extensions.enabled[^.]\+/d' | \
sed '/extensions.firefox@ghostery.com.sdk.rootURI/d' | \
sed '/extensions.sqlitemanager.jsonMruData/d' | \
sed '/extensions.{66E978CD-981F-47DF-AC42-E3CF417C1467}.sdk.\(baseURI\|load.reason\|domain\|rootURI\)/d' | \
sed '/extensions.xpiState/d' | \
sed '/print.print_to_filename/d' | \
sed '/browser.shell.mostRecentDateSetAsDefault/d' | \
sed '/browser.slowStartup.averageTime/d' | \
sed '/browser.slowStartup.samples/d' | \
sed '/extensions.blocklist.pingCount.*/d' | \
sed '/extensions.getAddons.cache.lastUpdate/d' | \
sed '/idle.lastDailyNotification/d' | \
sed '/toolkit.startup.last_success/d' | \
sed '/toolkit.telemetry.[^.]\+ID/d' | \
sed '/permissions.eventTelemetry.salt/d' | \
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
sed '/noscript.subscription.lastCheck/d' | \
sed '/noscript.version/d' | \
sed '/noscript.firstRunRedirection.pending/d' | \
sed '/noscript.ABE.cspHeaderDelim/d' | \
sed '/noscript.options.tabSelectedIndexes/d' | \
sed '/extensions.classicthemerestorer.pref_actindx/d' | \
sed '/extensions.classicthemerestorer.aboutprefs/d' | \
sed '/browser.uiCustomization.state/d' | \
sed '/browser.syncPromoViewsLeftMap/d' | \
sed '/\(gecko\|browser\).*\.mstone/d' | \
sed '/extensions.[^.]\+.sdk.version/d' | \
sed 's/\(browser.uiCustomization.state.*newElementCount[^:]*\): *[0-9]\+/\1:1/' | \
sed '/extensions.greasemonkey.version/d' | \
sed '/extensions.browsec.tracking_cid/d' | \
sed '/extensions.firefox@zenmate.com.sdk.version/d' | \
sed '/\(extensions.\)\?e10s.rollout/d' | \
sed '/extensions.webextensions.uuids/d' | \
sed '/media.gmp[.-]/d' | \
sed '/services.blocklist/d' | \
sed '/browser.startup.homepage_override.torbrowser.version/d' | \
sed '/browser.rights.3.shown/d' | \
sed '/extensions.pocket.settings.test.panelSignUp/d' | \
sed '/extensions..*.sdk.version/d' | \
sed '/browser.preferences.advanced.selectedTabIndex/d' | \
sed '/extensions.brief.update.lastUpdateTime/d' | \
sed '/storage.vacuum.last.brief.sqlite/d' | \
sed '/extensions.brief.database.lastPurgeTime/d' | \
sed '/extensions.blocklist.lastModified/d' | \
sed '/extensions.pendingOperations/d' | \
sed '/devtools.debugger.tabs/d' | \
sed '/devtools.debugger.pending-selected-location/d' | \
sed '/xpinstall.signatures.required/d' | \
sed '/distribution.iniFile.exists.appversion/d' | \
sed '/extensions.lastAppBuildId/d' | \
sed '/browser.safebrowsing.provider.google4.lastupdatetime/d' | \
sed '/browser.safebrowsing.provider.google4.nextupdatetime/d' | \
sed '/devtools.toolsidebar-width./d' | \
sed '/browser.cache.disk.amount_written/d' | \
sed '/services.settings.clock_skew_seconds/d' | \
sed '/services.settings.last_update_seconds/d' | \
sed '/services.settings.last_etag/d' | \
sed '/browser.cache.disk.telemetry_report_ID/d' | \
sed '/browser.startup.lastColdStartupCheck/d' | \
sed '/services.settings.main[.][a-z-]\+[.]last_check/d' | \
sed '/services.settings.security.onecrl.checked/d' | \
sed '/browser.bookmarks.editDialog.confirmationHintShowCount/d' | \
sed '/devtools.netmonitor.panes-network-details-height/d' | \
sed '/app.normandy.migrationsApplied/d' | \
sed '/app.normandy.user_id/d' | \
sed '/dom.push.userAgentID/d' | \
sed '/plugin.flash./d' | \
sed '/security.remote_settings.intermediates.checked/d' | \
sed '/security.remote_settings.crlite_filters.checked/d' | \
sed '/devtools.netmonitor.columnsData/d' | \
sed '/devtools.debugger.prefs-schema-version/d' | \
sed '/devtools.inspector.activeSidebar/d' | \
sed '/browser.protections_panel.infoMessage.seen/d' | \
sed '/browser.urlbar.placeholderName.private/d' | \
sed '/findbar.highlightAll/d' | \
sed '/browser.contentblocking.cfr-milestone/d' | \
sed '/pdfjs.enabledCache.state/d' | \
sed '/browser.urlbar.tipShownCount.searchTip_redirect/d' | \
sed '/devtools.netmonitor.persistlog/d' | \
sed '/devtools.toolbox.tabsOrder/d' | \
sed '/browser.download.lastDir/d' | \
sed '/media.benchmark.vp9./d' | \
sed 's/"extensions.systemAddonSet", "{.*");/"extensions.systemAddonSet", "{\\"schema\\":1,\\"addons\\":{}}");/' | \
sed '/browser.region.update.updated/d' | \
sed '/fission.experiment.max-origins[.]/d' | \
sed '/services.settings.main[.].*[.]last_check/d' | \
sed '/media.videocontrols.picture-in-picture.video-toggle.has-used/d' | \
sed '/"doh-rollout[.]/d' | \
sed '/devtools.debugger.expressions/d' | \
sed '/services[.]settings[.].*[.]last_check/d' | \
sed '/devtools.inspector.selectedSidebar/d' | \
sed '/browser.startup.couldRestoreSession.count/d' | \
sed '/devtools.performance.recording/d' | \
sed '/devtools[.]debugger[.][^.]*-visible/d' | \
sed '/privacy.sanitize.pending/d' | \
sed 's|'"$HOME"'|$HOME|g'
