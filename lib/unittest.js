// Simple unit test framework for testing JS utilities for Web pages.

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {}; 

if(!window.clckwrkbdgr['unittest']) window.clckwrkbdgr.unittest = {}; 

if(!window.clckwrkbdgr.unittest['results']) window.clckwrkbdgr.unittest.results = {};
if(!window.clckwrkbdgr.unittest['errors']) window.clckwrkbdgr.unittest.errors = {};

clckwrkbdgr.unittest.assertTrue = function(value)
{
	if(!value) {
		throw new Error('Expression is not True');
	}
}

clckwrkbdgr.unittest.assertFalse = function(value)
{
	if(value) {
		throw new Error('Expression is not False');
	}
}

function are_equal(a, b)
{
	if(Array.isArray(a) && Array.isArray(b)) {
		if(a.length != b.length) {
			return false;
		}
		for(var i = 0; i < a.length; ++i) {
			if(!are_equal(a[i], b[i])) {
				return false;
			}
		}
		return true;
	}
	return a === b;
}

clckwrkbdgr.unittest.assertEqual = function(actual, expected)
{
	if(!are_equal(actual, expected)) {
		throw new Error('Values are not equal: actual (' + JSON.stringify(actual) + ') != expected (' + JSON.stringify(expected) + ')');
	}
}

clckwrkbdgr.unittest.assertRaises = function(subfunc, exception_checker)
{
	var caught = false;
	try {
		subfunc();
	} catch(e) {
		if(exception_checker) {
			exception_checker(e);
		}
		caught = true;
	}
	if(!caught) {
		throw new Error('Exception was not thrown!');
	}
}

clckwrkbdgr.unittest.run_async_test_case = async function(test_case_name)
{
	// Looks exactly like plain run_test_case except for async/await keywords.
	try {
		await window[test_case_name]();
		document.querySelector('#unittest-result_' + test_case_name).textContent = 'OK';
		window.clckwrkbdgr.unittest.results[test_case_name] = true;
	} catch(e) {
		var error_text = e.toString() + '\n' + e.stack;
		document.querySelector('#unittest-result_' + test_case_name).textContent = 'Failed';
		document.querySelector('#unittest-details_' + test_case_name).textContent = error_text;
		window.clckwrkbdgr.unittest.results[test_case_name] = false;
		window.clckwrkbdgr.unittest.errors[test_case_name] = error_text;
	}
}

clckwrkbdgr.unittest.run_test_case = function(test_case_name)
{
	var need_teardown = false;
	try {
		if(window['setUp']) {
			window['setUp']();
		}
		need_teardown = true;
		window[test_case_name]();
		if(window['tearDown']) {
			window['tearDown']();
		}
		need_teardown = false;

		document.querySelector('#unittest-result_' + test_case_name).textContent = 'OK';
		window.clckwrkbdgr.unittest.results[test_case_name] = true;
	} catch(e) {
		var error_text = e.toString() + '\n' + e.stack;
		document.querySelector('#unittest-result_' + test_case_name).textContent = 'Failed';
		document.querySelector('#unittest-details_' + test_case_name).textContent = error_text;
		window.clckwrkbdgr.unittest.results[test_case_name] = false;
		window.clckwrkbdgr.unittest.errors[test_case_name] = error_text;

		if(need_teardown) {
			if(window['tearDown']) {
				window['tearDown']();
			}
			need_teardown = false;
		}
	}
}

clckwrkbdgr.unittest.run = function(prefix)
{
	if(prefix == undefined) {
		prefix = 'test_';
	}
	var main_div = document.querySelector('#unittest-main');
	var table = document.createElement('table');
	main_div.appendChild(table);
	var tbody = document.createElement('tbody');
	table.appendChild(tbody);

	var test_cases = [];
	for(var name in window) {
		if(name.startsWith('onmozfullscreen')) {
			continue; // Skipping deprecated properties.
		}
		var is_function = window.hasOwnProperty(name) && typeof window[name] === 'function';
		if(!is_function) {
			continue;
		}
		var is_unit_test_function = name.startsWith(prefix);
		if(!is_unit_test_function) {
			continue;
		}
		var tr = document.createElement('tr');
		tbody.appendChild(tr);
		var td = document.createElement('td');
		td.setAttribute('id', 'unittest-name_' + name);
		var a = document.createElement('a');
		a.textContent = name;
		a.setAttribute('href', '#');
		a.setAttribute('onclick', 'clckwrkbdgr.unittest.run_test_case("' + name + '");');
		td.appendChild(a);
		tr.appendChild(td);
		td = document.createElement('td');
		td.setAttribute('id', 'unittest-result_' + name);
		tr.appendChild(td);
		td = document.createElement('td');
		td.setAttribute('id', 'unittest-details_' + name);
		td.setAttribute('style', 'font-family: monospace; white-space: pre');
		tr.appendChild(td);

		test_cases.push(name);
	}
	var expected_promises = [];
	for(var i = 0; i < test_cases.length; ++i) {
		if(window[test_cases[i]][Symbol.toStringTag] == 'AsyncFunction') {
			// Async functions should be awaited for promised actual results.
			expected_promises.push(
				clckwrkbdgr.unittest.run_async_test_case(test_cases[i])
			);
		} else {
			clckwrkbdgr.unittest.run_test_case(test_cases[i]);
		}
	}

	(async function() {
		// If there were any async promises, we have to sync with them
		// to get actual unit testing results
		// and only then fill the table.
		for(var i = 0; i < expected_promises.length; ++i) {
			await expected_promises[i];
		}
		clckwrkbdgr.unittest._collect_results(tbody)
	})();
}

function send_post_request(endpoint, data, on_ok, on_fail)
{
	var xhttp = new XMLHttpRequest();
	xhttp.open("POST", endpoint, true);
	xhttp.setRequestHeader("Content-Type", "application/json");
	xhttp.onreadystatechange = function() {
		if (this.status == 200) {
			on_ok();
		} else {
			on_fail(this.status, this.responseText);
		}
	};
	xhttp.send(JSON.stringify(data));
}

clckwrkbdgr.unittest._collect_results = function(tbody)
{
	var total_success = 0;
	var total_failure = 0;
	var keys = Object.keys(clckwrkbdgr.unittest.results);
	for(var i = 0; i < keys.length; ++i) {
		if(clckwrkbdgr.unittest.results[keys[i]]) {
			++total_success;
		} else {
			++total_failure;
		}
	}
	clckwrkbdgr.unittest.success = (total_failure == 0);

	var empty_tr = document.createElement('tr');
	tbody.appendChild(empty_tr);
	var empty_td = document.createElement('td');
	empty_td.innerHTML = '<hr/>'
	empty_tr.appendChild(empty_td);

	var results = [
		['Successful', total_success],
		['Failed', total_failure],
	];
	for(var i = 0; i < results.length; ++i) {
		var value = results[i][1];
		if(!value) {
			continue;
		}
		var name = results[i][0];

		var tr = document.createElement('tr');
		tbody.appendChild(tr);
		var td = document.createElement('td');
		td.textContent = name;
		tr.appendChild(td);
		td = document.createElement('td');
		td.textContent = value;
		tr.appendChild(td);
	}

	send_post_request(window.location.href, {
		results: clckwrkbdgr.unittest.results,
		errors: clckwrkbdgr.unittest.errors
	}, function() {
		var urlParams = new URLSearchParams(window.location.search);
		var close_on_success = urlParams.get("close-on-success");
		if(clckwrkbdgr.unittest.success && close_on_success == "true")
		{
			window.close();
		}
	}, function(error_status, error_reason) {
		var tr = document.createElement('tr');
		tbody.appendChild(tr);
		var td = document.createElement('td');
		td.textContent = 'Failed to post results: ' + error_status + ' ' + error_reason;
		tr.appendChild(td);
	});

}
