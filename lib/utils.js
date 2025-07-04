// Library with base utilities.
// All functions/classes are available under namespace clckwrkbdgr.*

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};
if(!window.clckwrkbdgr['internal']) window.clckwrkbdgr.internal = {};

// If this library is used in userscripts which require some @grant permissions,
// modern browsers hide object `window` into sandbox and provide `unsafeWindow` instead,
// thus making `window.clckwrkbdgr` not available e.g. in the Developer Console.
// Following export routines make it available.

/** Exports given function in global window namespace.
 * This will also work for userscripts which work via unsafeWindow only.
 * If name is not specified, actual function name is used by default.
 */
clckwrkbdgr.export_function = function(func, name) {
	if(!name) {
		name = func.name;
	}
	window[name] = func;
	try {
		unsafeWindow[name] = window[name]
	} catch(e) {}
}

/** Exports given object (usually dict) in global window namespace.
 * This will also work for userscripts which work via unsafeWindow only.
 * Name must be specified explicitly in this case.
 */
clckwrkbdgr.export_object = function(object, name) {
	if(!name) {
		throw 'Cannot export object without name!';
	}
	window[name]= Object.assign({}, window[name], object);
	try {
		unsafeWindow[name]= Object.assign({}, unsafeWindow[name], window[name]);
	} catch(e) {}
}

window.clckwrkbdgr.debug = ''; // Switched off by default.

/** Sets trace parameters. */
clckwrkbdgr.set_trace = function(trace_category_pattern)
{
	window.clckwrkbdgr.debug = trace_category_pattern || '';
	clckwrkbdgr.storage.set('clckwrkbdgr.debug', JSON.stringify({
		category: window.clckwrkbdgr.debug
	}));
};

clckwrkbdgr._load_trace_setup = function()
{
	var loaded_debug_setup = JSON.parse(clckwrkbdgr.storage.get('clckwrkbdgr.debug', '{"category":""}'));
	window.clckwrkbdgr.debug = loaded_debug_setup.category;
}

/** Returns current trace parameters. */
clckwrkbdgr.get_trace = function()
{
	return window.clckwrkbdgr.debug;
};

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

/** Saves value to local storage in FS
 * so it can be accessed by other processes.
 *
 * If name is `undefined`, then value should be a batch dict of storage key:values.
 * If a single parameter is passed, it is considered as batch dict.
 *
 * It does by by CORS to http://localhost:20113/lib/save_to_fs_storage
 * so should be performed only from within userscripts
 * and requires additional @grant: GM.xmlHttpRequest (was GM_xmlhttpRequest).
 * In case of errors like "GM.xmlHttpRequest is not defined" check that other
 * userscripts have the same grant (looks like a bug in TamperMonkey?)
 */
clckwrkbdgr.storage.save_to_fs = function(name, value)
{
	if(value == undefined) {
		value = name;
		name = undefined;
	}
	var data = {
		domain: window.location.hostname,
		name: name,
		value: value,
	};
	var request = {
		method: "POST",
		url: "http://localhost:20113/lib/save_to_fs_storage",
		data: JSON.stringify(data),
		onload: function(res) {
			console.log(res);
		},
		onerror: function(res) {
			console.error(res);
		},
	};
	try {
		GM.xmlHttpRequest(request);
	} catch(e) {
		console.error(e);
		GM_xmlhttpRequest(request);
	}
	return true;
};

/** Returns full url to the favicon of the current site.
 */
clckwrkbdgr.get_favicon = function()
{
	var head_link = document.querySelector('link[rel="icon"]');
	if(!head_link) {
		head_link = document.querySelector('link[rel="shortcut icon"]');
	}
	if(!head_link) {
		return document.location.origin + "/favicon.ico";
	}
	head_link = head_link.href;
	if(head_link[0] == '/') {
		head_link = document.location.origin + head_link;
	}
	return head_link;
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
		var params = {
			body: text,
		};
		// If icon URL is not available, notification is SEVERELY slowed down or dropped completely.
		// As there is not way to mitigate this behavior in the Notification c-tor or at least cache icon,
		// just check if network is available - should cover most of such cases.
		if(window.navigator.onLine) {
			if(clckwrkbdgr._favicon == undefined) {
				clckwrkbdgr._favicon = clckwrkbdgr.get_favicon();
			}
			params.icon = clckwrkbdgr._favicon;
		}
		var notification = new Notification('[' + window.location.hostname + ']', params);
		notification = null;
		return true;
	} else if (Notification.permission !== "denied") {
		// Otherwise, we need to ask the user for permission
		Notification.requestPermission(function (permission) {
			// If the user accepts, let's create a notification
			if (permission === "granted") {
				var notification = new Notification('[' + window.location.hostname + ']', {body:text});
				notification = null;
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

/** Tries to save object from given URI.
 * If name is not specified, it will be deducated automatically.
 */
clckwrkbdgr.save_URI_as = function(uri, name)
{
	var link = document.createElement("a");
	link.download = name;
	link.href = uri;
	link.target = "_blank";
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	delete link;
};

/** Workaround for some older browsers that may not have function str.contains() */
clckwrkbdgr.internal.str_contains = function(str, startIndex)
{
	return -1 !== String.prototype.indexOf.call(this, str, startIndex);
};

if(!('contains' in String.prototype)) String.prototype.contains = clckwrkbdgr.internal.str_contains;

/** Workaround for some older browsers that may not have function str.trim() */
clckwrkbdgr.internal.str_trim = function()
{
	return String(this).replace(/^\s+|\s+$/g, '');
};
if(typeof(String.prototype.trim) === "undefined") String.prototype.trim = clckwrkbdgr.internal.str_trim;

/** Encodes HTML text into form safe to use within other HTML tags/attributes. */
clckwrkbdgr.htmlEncode = function(text)
{
	var element = document.createElement('a');
	var text_node = document.createTextNode(text);
	return element.appendChild(text_node).parentNode.innerHTML;
};

/** Decodes previous encoded HTML text. */
clckwrkbdgr.htmlDecode = function(text)
{
	var doc = new DOMParser().parseFromString(text, "text/html");
	return doc.documentElement.textContent;
};

/** Fires callback indefinitely with given timeout.
 * Returns timer ID, so it can be stopped by: clearInterval(id) & id=null;
 */
clckwrkbdgr.repeat = function(timeout, callback)
{
	return setInterval(function() {
		try {
			callback();
		} catch(e) {
			console.error(e);
		}
	}, timeout);
}

/** Returs True if two objects (dicts) have equal content.
 */
clckwrkbdgr.objects_equal = function(a, b)
{
	for(var k in a) {
		if(a.hasOwnProperty(k) != b.hasOwnProperty(k)) {
			// B has no property k.
			return false;
		}
		if(typeof a[k] != typeof b[k]) {
			// Different types for k.
			return false;
		}
	}
	for(var k in b) {
		if(b.hasOwnProperty(k) != a.hasOwnProperty(k)) {
			// A has no property k.
			return false;
		}
		if(typeof b[k] != typeof a[k]) {
			// Different types for k.
			return false;
		}
		if(a[k] instanceof Array) {
			if(JSON.stringify(a[k]) != JSON.stringify(b[k])) {
				// Lists differ.
				return false;
			}
		} else if(a[k] instanceof Object) {
			if(!clckwrkbdgr.objects_equal(a[k], b[k])) {
				// Sub-objects differ.
				return false;
			}
		} else if(a[k] != b[k]) {
			// Values differ.
			return false;
		}
	}
	// Look equal.
	return true;
}

////////////////////////////////////////////////////////////////////////////////
clckwrkbdgr.export_object(clckwrkbdgr, 'clckwrkbdgr');
// Load persistent debug level.
clckwrkbdgr._load_trace_setup();
