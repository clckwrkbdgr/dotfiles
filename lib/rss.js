// Library with utilities for processing RSS and feeds.
// All functions/classes are available under namespace clckwrkbdgr.rss.*

// TODO requires ./utils.js

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};
if(!window.clckwrkbdgr['rss']) window.clckwrkbdgr.rss = {};

var TRACE = clckwrkbdgr.tracer('rss');

/** Runs specified handler function only when URL anchor fully matches given pattern.
 * Pattern can be either string or regex.
 * If regex contains groups, matched parts will be passed to handler as parameters.
 */
clckwrkbdgr.rss.on_anchor = function(pattern, handler, _options)
{
	var url = new URL(_options['href'] || window.location.href);
	var anchor = url.hash.substr(1);
	var match = false;
	if(typeof pattern === 'string' || pattern instanceof String) {
		match = anchor == pattern ? anchor : null;
	} else {
		match = anchor.match(pattern);
		if(match && match[0].length != anchor.length) {
			match = null
		}
	}
	if(!match) {
		TRACE('Not a #' + pattern + ' target.');
		return false;
	}
	var args = match.slice(1);
	return handler(...args);
};

/** Waits until user-defined watcher action succeeds (with repeat_timeout), and then closes the window.
 * Useful for automation of some 'refreshing' actions, like updating cookies and checking some data on a website.
 * To stop watcher process just throw any exception.
 *
 * Handler is an optional funciton to call when finished watching. Default is window.close.
 * NOTE: window.close() would no work in Firefox without about:config: dom.allow_scripts_to_close_windows=true
 */
clckwrkbdgr.rss.collect = function(watcher, repeat_timeout, handler, _options)
{
	if(!handler) {
		handler = function() { TRACE('Closing window...'); window.close(); };
	}
	try {
		var finished = watcher();
		if(finished) {
			TRACE('Finished watching, taking action...');
			handler();
			return true;
		}
		TRACE('Still watching...');
		(_options['setTimeout'] || setTimeout)(function() {
			return clckwrkbdgr.rss.collect(watcher, repeat_timeout, handler, _options);
		}, repeat_timeout);
		return false;
	} catch(e) {
		console.error(e);
	}
};

////////////////////////////////////////////////////////////////////////////////
// Is this library is used in userscripts which require some @grant permissions,
// modern browsers hide object `window` into sandbox and provide `unsafeWindow` instead,
// thus making `window.clckwrkbdgr` not available e.g. in the Developer Console.
// This export statement makes it available.
try {
   unsafeWindow.clckwrkbdgr = Object.assign({}, unsafeWindow.clckwrkbdgr, window.clckwrkbdgr);
} catch(e) {}
