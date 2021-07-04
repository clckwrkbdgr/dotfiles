// Simple unit test framework for testing JS utilities for Web pages.

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {}; 

if(!window.clckwrkbdgr['unittest']) window.clckwrkbdgr.unittest = {}; 

clckwrkbdgr.unittest.assertTrue = function(value)
{
	if(!value) {
		throw new Error('Expression is not True');
	}
}

clckwrkbdgr.unittest.assertEqual = function(actual, expected)
{
	if(actual != expected) {
		throw new Error('Values are not equal: actual (' + JSON.stringify(actual) + ') != expected (' + JSON.stringify(expected) + ')');
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
		td.textContent = name;
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
		var test_case = test_cases[i];
		try {
			window[test_case]();
			document.querySelector('#unittest-result_' + test_case).textContent = 'OK';
		} catch(e) {
			document.querySelector('#unittest-result_' + test_case).textContent = 'Failed';
			document.querySelector('#unittest-details_' + test_case).textContent = e.toString() + '\n' + e.stack;
		}
	}
}
