// Library with base utilities.
// All functions/classes are available under namespace clckwrkbdgr.*

window.clckwrkbdgr = {}; 

clckwrkbdgr.storage = {};

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
}

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
}
