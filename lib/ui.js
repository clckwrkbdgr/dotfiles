// Library for creation (mostly injection) of simple UI.
// All functions/classes are available under namespace clckwrkbdgr.ui.*

// TODO requires ./utils.js

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};
if(!window.clckwrkbdgr['ui']) window.clckwrkbdgr.ui = {};

var trace = clckwrkbdgr.tracer('ui');

/** Creates container for GUI controls and places it into the given root element.
 *
 * If root_element is not an Element but a selector string
 * and such selector is not yet avaialable, will wait until it is.
 *
 * Controls is an array of definition structs:
 * - type: type of UI element to be created;
 *   Function with name 'create_<type>' should exist, e.g. 'create_button'.
 * - args: array of arguments to be passed to creation function;
 *
 * Available options:
 * - type: Type of the container element, allowed values: ul, div. By default is div.
 *   If type is <ul>, subcontrols are wrapped into <li> items.
 * - id: ID of the created container.
 * - class_name: Class of the created container.
 * - style: Custom style for the created container.
 * - prepend: If True, prepends container to the beginning of the root element, otherwise (default) appends to the end.
 */
clckwrkbdgr.ui.create_gui_container = function(root_element, options, controls)
{
	if(!(root_element instanceof Element)) {
		trace('Not an Element, so supposed to be a selector: ' + root_element);
		var actual_element = document.querySelector(root_element);
		if(actual_element) {
			root_element = actual_element;
		} else {
			trace('Does not exist yet, waiting...');
			setTimeout(function() {
				clckwrkbdgr.create_gui_container(root_element, options, controls);
			}, 100);
			return;
		}
	}

	var container;
	var subcontainer_type;
	if(options['type'] == 'ul') {
		container = document.createElement('ul');
		subcontainer_type = 'li';
	} else if(options['type'] == 'li') {
		container = document.createElement('li');
	} else {
		container = document.createElement('div');
	}

	if(options['id']) {
		container.setAttribute('id', options['id']);
	}

	if(options['class_name']) {
		container.classList.add(options['class_name']);
	}

	if(options['style']) {
		container.setAttribute('style', options['style']);
	}

	for(var i = 0; controls && i < controls.length; ++i) {
		var control_def = controls[i];
		var constructor = clckwrkbdgr.ui['create_' + control_def['type']];
		var args = control_def['args'] || [];
		var control = constructor(...args);

		if(subcontainer_type) {
			var subcontainer = document.createElement(subcontainer_type);
			subcontainer.appendChild(control);
			control = subcontainer;
		}
		container.appendChild(control);
	}

	if(options['prepend']) {
		root_element.insertBefore(container, root_element.firstChild);
	} else {
		root_element.appendChild(container);
	}
	return container;
};

/** Creates and returns clickable div element.
 * Onclick is a handler that takes clicked Element as argument.
 * Available options:
 * - id;
 * - class_name;
 * - style.
 */
clckwrkbdgr.ui.create_menu_item = function(text, onclick, options)
{
	var menu_item = document.createElement('div');
	if(options['id']) {
		menu_item.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		menu_item.classList.add(options['class_name']);
	}
	if(options['style']) {
		menu_item.setAttribute('style', options['style']);
	}
	menu_item.innerText = text;
	menu_item.addEventListener('click', function(e) { onclick(e.target) });
	return menu_item;
};

/** Creates and returns plain text info element.
 * Available options:
 * - id;
 * - type: default is <div>;
 * - class_name.
 * - style.
 */
clckwrkbdgr.ui.create_info_item = function(text, options)
{
	var element_type = 'div';
	if(options['type']) {
		element_type = options['type'];
	}
	var info = document.createElement(element_type);
	if(options['id']) {
		info.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		info.classList.add(options['class_name']);
	}
	if(options['style']) {
		info.setAttribute('style', options['style']);
	}
	info.innerText = text;
	return info;
};

/** Creates and return clickable button with caption.
 * Available options:
 * - id;
 * - class_name;
 * - type: default is <button>;
 *   If type is <a>, the role="button" is added.
 * - onclick: onclick handler;
 */
clckwrkbdgr.ui.create_button = function(caption, options)
{
	var element_type = 'button';
	if(options['type']) {
		element_type = options['type'];
	}
	var button = document.createElement(element_type);
	if(element_type == 'a') {
		button.setAttribute('role', 'button');
		button.setAttribute('href', 'javascript:void(0)');
	}
	if(options['id']) {
		button.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		button.classList.add(options['class_name']);
	}
	if(options['style']) {
		button.setAttribute('style', options['style']);
	}
	if(options['onclick']) {
		button.addEventListener('click', function(e) { options['onclick'](e.target) });
	}
	button.innerText = caption;
	return button;
};

/** Creates and return clickable button with multiple states.
 * Each state is a dict of properties:
 * - value: internal value of the state.
 * - caption;
 * - style;
 * - class_name;
 * - onchange: handler that is called when state is switched on;
 * Default state is the first one in the list.
 * Available options:
 * - id;
 * - type: default is <button>;
 *   If type is <a>, the role="button" is added.
 */
clckwrkbdgr.ui.create_multistate_button = function(states, options)
{
	var element_type = 'button';
	if(options['type']) {
		element_type = options['type'];
	}
	var button = document.createElement(element_type);
	if(element_type == 'a') {
		button.setAttribute('role', 'button');
		button.setAttribute('href', '#');
	}
	if(options['id']) {
		button.setAttribute('id', options['id']);
	}
	button.states = states;
	button.addEventListener('click', function() {
		try {
			var current_value = button.getAttribute('clckwrkbdgr-value');

			var next_state;
			if(current_value == undefined) {
				next_state = states[0];
			} else {
				var state_index;
				for(state_index = 0; state_index < states.length; ++state_index) {
					if(states[state_index]['value'] == current_value) {
						break;
					}
				}
				if(state_index >= states.length) {
					throw Exception('Cannot find state in button: ' + current_value)
				}
				++state_index;
				if(state_index >= states.length) {
					state_index = 0;
				}
				next_state = states[state_index];
				if(next_state.onchange) {
					next_state.onchange();
				}
			}
			button.classList = [];
			button.classList.add(next_state['class_name']);
			button.setAttribute('style', next_state['style']);
			button.setAttribute('clckwrkbdgr-value', next_state['value']);
			button.innerText = next_state['caption'];
		} catch(e) {
			console.error(e);
		}
	});
	button.click();
	return button;
};

/** Set multistate button to a specific state.
 */
clckwrkbdgr.ui.set_multistate_button_state = function(button, value)
{
	var states = button.states;
	var state_index;
	for(state_index = 0; state_index < states.length; ++state_index) {
		if(states[state_index]['value'] == value) {
			break;
		}
	}
	if(state_index >= states.length) {
		throw Exception('Cannot find state in button: ' + value)
	}
	var next_state = states[state_index];
	if(next_state.onchange) {
		next_state.onchange();
	}
	button.classList = [];
	button.classList.add(next_state['class_name']);
	button.setAttribute('style', next_state['style']);
	button.setAttribute('clckwrkbdgr-value', next_state['value']);
	button.innerText = next_state['caption'];
};

/** Toggles visibility state of the element.
 * Element can be either actual element, or query selector.
 * Optional visible_style is used to specify non-"none" state.
 * By default is "block".
 */
clckwrkbdgr.ui.toggle_visibility = function(element, visible_style)
{
	if(!(element instanceof Element)) {
		element = document.querySelector(element);
	}
	if(!visible_style) {
		visible_style = "block";
	}
	var display_style = element.style.display;
	element.style.display = (display_style == "none") ? visible_style : "none";
};

/** Creates simple link with given href and text.
 * Available options:
 * - id;
 * - class_name;
 * - style.
 */
clckwrkbdgr.ui.create_link = function(href, text, options)
{
	if(options == undefined) {
		options = {};
	}
	var link = document.createElement('a');
	link.setAttribute('target', '_blank');
	link.setAttribute('href', href);
	link.innerText = text;
	if(options['id']) {
		link.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		link.classList.add(options['class_name']);
	}
	if(options['style']) {
		link.setAttribute('style', options['style']);
	}
	return link
};

/** Creates spin edit for integer values.
 * If min_value is undefined, it defaults to 1.
 * IF max_value is undefined, spinning is not limited from the top.
 * If default value is omitted, min_value is used.
 *
 * Spin edit is controlled by two buttons: for decrement and for increment.
 * There is also option to click on label to display dialog to input specific value directly.
 *
 * Available options:
 * - id: the id of the element which stores and displays target value;
 *   The container will have id="<id>-container"
 *   The title span will have id="<id>-title"
 *   The dec button will have id="<id>-dec"
 *   The inc button will have id="<id>-inc"
 * - class_name: class of caption and label elements;
 * - class_down: class of dec button;
 *   if omitted and 'class_name' specified, it will be used instead.
 * - class_up: class of inc button;
 *   if omitted and 'class_name' specified, it will be used instead.
 * - style: class for caption and label elements;
 * - style-down: style of dec button;
 *   if omitted and 'class_name' specified, it will be used instead.
 * - style-up: style of inc button;
 *   if omitted and 'class_name' specified, it will be used instead.
 * - onchange: handler function which is called each time value is changed.
 *   Should accept single argument: new value.
 */
clckwrkbdgr.ui.create_spin = function(title, min_value, max_value, default_value, options)
{
	if(min_value == undefined) {
		min_value = 1;
	}
	if(default_value == undefined) {
		default_value = 1;
	}
	if(default_value < min_value) {
		default_value = min_value;
	}

	var container = document.createElement('div');
	if(options['id']) {
		container.setAttribute('id', options['id'] + '-container');
	}

	var caption = document.createElement('span');
	if(options['id']) {
		caption.setAttribute('id', options['id'] + '-title');
	}
	if(options['class_name']) {
		caption.classList.add(options['class_name']);
	}
	if(options['style']) {
		caption.setAttribute('style', options['style']);
	}
	caption.innerText = title;
	container.appendChild(caption);

	var button_down = document.createElement('div');
	if(options['id']) {
		button_down.setAttribute('id', options['id'] + '-dec');
	}
	if(options['class_down']) {
		button_down.classList.add(options['class_down']);
	} else if(options['class_name']) {
		button_down.classList.add(options['class_name']);
	}
	if(options['style_down']) {
		button_down.setAttribute('style', options['style_down']);
	} else if(options['style']) {
		button_down.setAttribute('style', options['style']);
	}
	button_down.innerText = '-';
	container.appendChild(button_down);

	var label = document.createElement('span');
	if(options['id']) {
		label.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		label.classList.add(options['class_name']);
	}
	if(options['style']) {
		label.setAttribute('style', options['style']);
	}
	label.innerText = default_value;
	container.appendChild(label);

	var button_up = document.createElement('div');
	if(options['id']) {
		button_up.setAttribute('id', options['id'] + '-inc');
	}
	if(options['class_up']) {
		button_up.classList.add(options['class_up']);
	} else if(options['class_name']) {
		button_up.classList.add(options['class_name']);
	}
	if(options['style_up']) {
		button_up.setAttribute('style', options['style_up']);
	} else if(options['style']) {
		button_up.setAttribute('style', options['style']);
	}
	button_up.innerText = '+';
	container.appendChild(button_up);

	button_down.addEventListener('click', function() {
		var value = parseInt(label.innerText);
		if(value > min_value) {
			--value;
		} else {
			value = min_value;
		}
		label.innerText = value.toString();
		if(options['onchange']) {
			options['onchange'](value);
		}
	});
	button_up.addEventListener('click', function() {
		var value = parseInt(label.innerText);
		if(max_value == undefined || value < max_value) {
			++value;
		} else {
			value = max_value;
		}
		label.innerText = value.toString();
		if(options['onchange']) {
			options['onchange'](value);
		}
	});
	label.addEventListener('click', function() {
		var value = parseInt(label.innerText);
		value = window.prompt(title, value);
		if(value == null) {
			return;
		}
		label.set_value(value);
	});
	label.set_value = function(new_value) {
		try {
			new_value = parseInt(new_value);
		} catch(e) {
			return;
		}
		if(new_value < min_value) {
			new_value = min_value;
		}
		if(max_value != undefined && new_value > max_value) {
			new_value = max_value;
		}
		label.innerText = new_value.toString();
		if(options['onchange']) {
			options['onchange'](new_value);
		}
	};

	return container;
};

/** Programmatically changes spin value.
 * Constrains are checked and onchange handler is emitted.
 */
clckwrkbdgr.ui.set_spin_value = function(spin_id, new_value)
{
	var label = document.querySelector('#' + spin_id);
	label.set_value(new_value);
};

/** Creates checkbox with given title.
 * Available options:
 * - id: the id of the input element.
 * - name: the name of the input element; if not specified, .id is used.
 * - class_name: the class of the input element.
 * - style;
 * - label_class_name: the class of the corresponding label element.
 * - onchange: function with single parameter 'new_state',
 *   which will be called when checkbox changes state.
 */
clckwrkbdgr.ui.create_checkbox = function(title, options)
{
	var container = document.createElement('div');

	var checkbox = document.createElement('input');
	checkbox.setAttribute('type', 'checkbox');
	if(options['id']) {
		checkbox.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		checkbox.classList.add(options['class_name']);
	}
	if(options['style']) {
		container.setAttribute('style', options['style']);
	}
	if(options['name']) {
		checkbox.setAttribute('name', options['name']);
	} else if(options['id']) {
		checkbox.setAttribute('name', options['id']);
	}
	if(options['onchange']) {
		checkbox.addEventListener('change', function(event) {
			options['onchange'](event.target.checked);
		});
	}
	container.appendChild(checkbox);

	var label = document.createElement('label');
	if(options['id']) {
		label.setAttribute('for', options['id']);
	}
	if(options['label_class_name']) {
		label.classList.add(options['label_class_name']);
	}
	label.innerText = title;
	container.appendChild(label);

	return container;
};

/** Creates input element for loading files with given label title.
 * Available options:
 * - id: the id of the input element.
 * - class_name: the class of the input element.
 * - label_class_name: the class of the corresponding label element.
 * - onload: function to process loaded file.
 *   Accepts single parameter 'file_contents'.
 */
clckwrkbdgr.ui.create_file_input = function(title, options)
{
	var container = document.createElement('div');

	var file_input = document.createElement('input');
	file_input.setAttribute('type', 'file');
	if(options['id']) {
		file_input.setAttribute('id', options['id']);
	}
	if(options['class_name']) {
		file_input.classList.add(options['class_name']);
	}
	if(options['onload']) {
		file_input.onclick = function() {
			this.value = null;
		};
		file_input.onchange = function(event) {
			var fr = new FileReader();
			fr.onload = function(file_event) {
				if(typeof(file_event) === 'undefined') {
					file_event = undefined;
				}
				if(file_event != undefined) {
					var file_contents = file_event.target.result;
					options['onload'](file_contents);
				} else {
					console.error('Failed to load file:', file_event);
				}
			}
			fr.readAsText(event.target.files[0]);
		};
	}
	container.appendChild(file_input);

	var label = document.createElement('label');
	if(options['id']) {
		label.setAttribute('for', options['id']);
	}
	if(options['label_class_name']) {
		label.classList.add(options['label_class_name']);
	}
	label.innerText = title;
	container.appendChild(label);

	return container;
};

////////////////////////////////////////////////////////////////////////////////
clckwrkbdgr.export_object(clckwrkbdgr, 'clckwrkbdgr');
