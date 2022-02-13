// Library with base utilities.
// All functions/classes are available under namespace clckwrkbdgr.*

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};

window.clckwrkbdgr.debug = ''; // Switched off by default.

/** Creates traces for given category if corresponding trace_category is set in variable window.clckwrkbdgr.debug.
 * Variable may contain only heading part of the trace category, so all categories starting with that prefix will be on.
 * By default console.log is used as logger.
 * If prefix_generator is specified, it should be a function with no arguments that return prefix for log messages
 * (e.g. time or some id).
 * Trace category is already applied as a prefix: "<prefix> <category>: <message>"
 * If message is not a string, it will be treated and printed as JSON object.
 */
clckwrkbdgr.tracer = function(trace_category, prefix_generator, logger)
{
	if(!logger) {
		logger = console.log;
	}
	if(!trace_category) {
		trace_category = '';
	}
	return function(message) {
		var to_print = false;
		if(trace_category == '') {
			to_print = true;
		} else if(window.clckwrkbdgr.debug == '') {
			to_print = false;
		} else if(trace_category.startsWith(window.clckwrkbdgr.debug)) {
			to_print = true;
		}
		if(!to_print) {
			return;
		}
		var prefix = '';
		if(prefix_generator) {
			prefix += prefix_generator() + ' ';
		}
		if(typeof message !== 'string') {
			message = JSON.stringify(message);
		}
		logger(prefix + trace_category + ': ' + message);
	}
};

if(!window.clckwrkbdgr['storage']) window.clckwrkbdgr.storage = {};

/** Safely sets value in local storage. */
clckwrkbdgr.storage.set = function(name, value)
{
	try {
		window.localStorage.setItem(name, value);
		return true;
	} catch(e) {
		console.error(e);
		return false;
	}
};

/** Safely retrieves value from local storage.
 * If value is absent, default values is returned instead.
 */
clckwrkbdgr.storage.get = function(name, default_value)
{
	try {
		var value = window.localStorage.getItem(name);
		if(value == null)
		{
			value = default_value;
		}
		return value;
	} catch(e) {
		console.error(e);
	}
	return default_value;
};

/** Displays system notification.
 * May explicitly ask for permissions if they were not given yet for current site.
 */
clckwrkbdgr.notify = function(text)
{
	// Let's check if the browser supports notifications
	if (!("Notification" in window)) {
		console.log("This browser does not support desktop notification");
		return false;
	} else if (Notification.permission === "granted") {
		// Let's check whether notification permissions have already been granted
		// If it's okay let's create a notification
		var notification = new Notification(text);
		return true;
	} else if (Notification.permission !== "denied") {
		// Otherwise, we need to ask the user for permission
		Notification.requestPermission(function (permission) {
			// If the user accepts, let's create a notification
			if (permission === "granted") {
				var notification = new Notification(text);
			}
		});
		return false;
	} else {
		// At last, if the user has denied notifications, and you
		// want to be respectful there is no need to bother them any more.
		console.log('No permissions to show notification. Text:' + text);
		return false;
	}
};
