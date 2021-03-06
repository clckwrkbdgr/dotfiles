// Simple unit test framework for testing JS utilities for Web pages.

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {}; 

if(!window.clckwrkbdgr['unittest']) window.clckwrkbdgr.unittest = {}; 

clckwrkbdgr.unittest.assertTrue = function(value)
{
	if(!value) {
		throw new Error('Expression is not True');
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

clckwrkbdgr.unittest.run_test_case = function(test_case_name)
{
	try {
		window[test_case_name]();
		document.querySelector('#unittest-result_' + test_case_name).textContent = 'OK';
	} catch(e) {
		document.querySelector('#unittest-result_' + test_case_name).textContent = 'Failed';
		document.querySelector('#unittest-details_' + test_case_name).textContent = e.toString() + '\n' + e.stack;
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
		var is_unit_test_function = name.startsWith(prefix) || name == 'setUp' || name == 'tearDown';
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
	for(var i = 0; i < test_cases.length; ++i) {
		clckwrkbdgr.unittest.run_test_case(test_cases[i]);
	}
}
