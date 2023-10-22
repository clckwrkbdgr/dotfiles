// Library for creation (mostly injection) of simple UI.
// All functions/classes are available under namespace clckwrkbdgr.autoidle.*

// TODO requires ./utils.js

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};
if(!window.clckwrkbdgr['autoidle']) window.clckwrkbdgr.autoidle = {};

function is_dict(value)
{
	return value && value.constructor == Object;
}

clckwrkbdgr.autoidle = {};
clckwrkbdgr.autoidle._config = {};
clckwrkbdgr.autoidle._enable_all = true;
clckwrkbdgr.autoidle._triggers_registry = {};
clckwrkbdgr.autoidle._actions_registry = {};
clckwrkbdgr.autoidle._watchers_registry = {};
clckwrkbdgr.autoidle._watchers = {};
clckwrkbdgr.autoidle._watchers_changed = {};
clckwrkbdgr.autoidle._rules = [];

clckwrkbdgr.autoidle._on_open_settings = undefined;
clckwrkbdgr.autoidle._on_close_settings = undefined;

/// GUI ////////////////////////////////////////////////////////////////////////

var default_dialog_style = `
#clckwrkbdgr-autoidle-modal, #clckwrkbdgr-autoidle-modal * {
	box-sizing: content-box;
}
`;

/** Creates modal settings dialog.
 */
clckwrkbdgr.autoidle._create_settings_modal = function()
{
	// Main background div.
	var autoidle_modal_div = document.createElement('div');
	autoidle_modal_div.setAttribute('id', 'clckwrkbdgr-autoidle-modal');
	autoidle_modal_div.style.display = 'none';
	autoidle_modal_div.style.position = "fixed";
	autoidle_modal_div.style['z-index'] = "100";
	autoidle_modal_div.style.left = "0px";
	autoidle_modal_div.style.top = "0px";
	autoidle_modal_div.style.width = "100vw";
	autoidle_modal_div.style.height = "100vh";
	autoidle_modal_div.style['background-color'] = "rgba(0, 0, 0, 0.5)";

	// Main dialog window.
	var autoidle_window = document.createElement('div');
	autoidle_window.style.margin = "2%";
	autoidle_window.style['background-color'] = "#333";
	autoidle_window.style.padding = "10px";
	autoidle_window.style.border = "1px solid yellow";
	autoidle_window.style.width = "96vw";
	autoidle_window.style.height = "90vh";

	// Window header.
	var autoidle_window_header = document.createElement('ul');
	autoidle_window_header.style.padding = "10px";
	autoidle_window_header.style.display = "flex";
	autoidle_window_header.style.width = '95vw';
	autoidle_window_header.style['border-bottom'] = '1px solid yellow';
	autoidle_window.appendChild(autoidle_window_header);

	// Window title and place for control buttons.
	var autoidle_window_title = document.createElement('p');
	autoidle_window_title.innerText = 'AutoIdle';
	var autoidle_window_title_li = document.createElement('li');
	autoidle_window_title_li.style.display = "flex";
	autoidle_window_title_li.style.width = "95vw";
	autoidle_window_title_li.appendChild(autoidle_window_title);
	autoidle_window_header.appendChild(autoidle_window_title_li);

	// Button OK - save and close.
	var save_autoidle_window = document.createElement('a');
	save_autoidle_window.innerText = 'OK';
	save_autoidle_window.setAttribute('onclick', 'clckwrkbdgr.autoidle._close_settings(true); return false;');
	var save_autoidle_window_li = document.createElement('li');
	save_autoidle_window_li.style.display = "flex";
	save_autoidle_window_li.style.border = "1px yellow solid";
	save_autoidle_window_li.style.padding = "5px";
	save_autoidle_window_li.style.margin = "5px";
	save_autoidle_window_li.appendChild(save_autoidle_window);
	autoidle_window_header.appendChild(save_autoidle_window_li);

	// Button Cancel - close without saving.
	var cancel_autoidle_window = document.createElement('a');
	cancel_autoidle_window.innerText = 'Cancel';
	cancel_autoidle_window.setAttribute('onclick', 'clckwrkbdgr.autoidle._close_settings(); return false;');
	var cancel_autoidle_window_li = document.createElement('li');
	cancel_autoidle_window_li.style.display = "flex";
	cancel_autoidle_window_li.style.border = "1px yellow solid";
	cancel_autoidle_window_li.style.padding = "5px";
	cancel_autoidle_window_li.style.margin = "5px";
	cancel_autoidle_window_li.appendChild(cancel_autoidle_window);
	autoidle_window_header.appendChild(cancel_autoidle_window_li);

	// Common window area.
	var autoidle_window_main_settings = document.createElement('ul');
	autoidle_window_main_settings.style.padding = "10px";
	autoidle_window_main_settings.style.display = "flex";
	autoidle_window_main_settings.style.width = '95vw';
	autoidle_window_main_settings.style['border-bottom'] = '1px solid yellow';
	autoidle_window.appendChild(autoidle_window_main_settings);

	// Meta controls.
	var autoidle_window_enable_all = document.createElement('input');
	autoidle_window_enable_all.setAttribute('type', 'checkbox');
	autoidle_window_enable_all.setAttribute('id', 'clckwrkbdgr-autoidle-enable-all');
	autoidle_window_enable_all.setAttribute('name', 'clckwrkbdgr-autoidle-enable-all');
	autoidle_window_main_settings.appendChild(autoidle_window_enable_all);
	var autoidle_window_enable_all_label = document.createElement('label');
	autoidle_window_enable_all_label.setAttribute('for', 'clckwrkbdgr-autoidle-enable-all');
	autoidle_window_enable_all_label.innerText = 'Enable all';
	autoidle_window_main_settings.appendChild(autoidle_window_enable_all_label);

	var autoidle_export_button = document.createElement('a');
	autoidle_export_button.innerText = 'Export';
	autoidle_export_button.addEventListener("click", function() {
		clckwrkbdgr.autoidle._save_file(
			JSON.stringify(clckwrkbdgr.autoidle._export_settings()),
			'autoidle-export.' + window.location.hostname + '.json',
		);
	});
	autoidle_window_main_settings.appendChild(autoidle_export_button);

	var autoidle_import_button = document.createElement('a');
	autoidle_import_button.innerText = 'Import';
	autoidle_import_button.addEventListener("click", function() {
		clckwrkbdgr.autoidle._open_file(
			function(rules_string) {
				clckwrkbdgr.autoidle._import_settings(JSON.parse(rules_string));
			}
		);
	});
	autoidle_window_main_settings.appendChild(autoidle_import_button);

	// Main working area.
	var autoidle_content = document.createElement('div');
	autoidle_content.setAttribute('id', 'clckwrkbdgr-autoidle');
	autoidle_content.style.width = "95vw";
	autoidle_content.style.height = "65vh";
	autoidle_content.style['overflow-x'] = "hidden";
	autoidle_content.style['overflow-y'] = "auto";
	autoidle_window.appendChild(autoidle_content);

	// Combine dialog.
	autoidle_modal_div.appendChild(autoidle_window);
	document.body.appendChild(autoidle_modal_div);
	return autoidle_modal_div;
}

/** Opens settings dialog.
 */
clckwrkbdgr.autoidle.open_settings = function()
{
	// User-defined action.
	if(clckwrkbdgr.autoidle._on_open_settings) {
		try {
			clckwrkbdgr.autoidle._on_open_settings();
		} catch(e) {
			console.error(e);
		}
	}

	// Find or create modal dialog.
	var autoidle_modal_div = document.querySelector('#clckwrkbdgr-autoidle-modal');
	if(!autoidle_modal_div) {
		autoidle_modal_div = clckwrkbdgr.autoidle._create_settings_modal();
	}

	// Add custom css.
	var custom_styles = document.createElement('style');
	custom_styles.innerText = default_dialog_style;
	document.head.appendChild(custom_styles);

	// Init 'Enable all' checkbox.
	var autoidle_window_enable_all = document.querySelector('#clckwrkbdgr-autoidle-enable-all');
	autoidle_window_enable_all.checked = clckwrkbdgr.autoidle._enable_all;

	// Fill rules.
	clckwrkbdgr.autoidle._fill_rules_widgets(
		document.querySelector('#clckwrkbdgr-autoidle'),
		clckwrkbdgr.autoidle._rules,
	);

	// Behold.
	autoidle_modal_div.style.display = 'block';
}

/** Exports current set of rules from the modal dialog to a dict.
 */
clckwrkbdgr.autoidle._export_settings = function()
{
	var data = [];

	var container = document.querySelector('#clckwrkbdgr-autoidle');
	var all_rules = container.querySelectorAll('div.clckwrkbdgr-rule');
	for(var i = 0; i < all_rules.length; ++i) {
		var rule = {
			enabled: false,
			triggers: [],
			action: null,
		};
		var rule_div = all_rules[i];
		var current_index = +(rule_div.getAttribute('data-rule-index'));

		var rule_enabled = rule_div.querySelector('#clckwrkbdgr-autoidle-enable-rule-' + current_index);
		rule.enabled = rule_enabled.checked;

		var triggers = rule_div.querySelectorAll('div.clckwrkbdgr-auto-trigger-row');
		for(var j = 0; j < triggers.length; ++j) {
			var trigger = triggers[j];
			var trigger_name = trigger.querySelector('select.clckwrkbdgr-trigger-name').value;
			var trigger_data = clckwrkbdgr.autoidle._triggers_registry[trigger_name];
			if(!trigger_data.param_type) {
				rule.triggers.push(trigger_name);
				continue;
			}
			var compare_function = trigger.querySelector('select.clckwrkbdgr-trigger-compare-function').value;
			var trigger_value = trigger.querySelector('input.clckwrkbdgr-trigger-value').value;
			rule.triggers.push([trigger_name, compare_function, trigger_value]);
		}

		var action = rule_div.querySelector('select.clckwrkbdgr-rule-action').value;
		var action_parameters = rule_div.querySelectorAll('input.clckwrkbdgr-rule-parameter');
		if(action_parameters.length > 0) {
			action = [action];
			for(var j = 0; j < action_parameters.length; ++j) {
				action.push(action_parameters[j].value);
			}
			rule.action = action
		} else {
			rule.action = action;
		}

		data.push(rule);
	}
	return data;
}

/** Imports rules from data and re-sets current autoidle dialog.
 */
clckwrkbdgr.autoidle._import_settings = function(rules)
{
	clckwrkbdgr.autoidle._fill_rules_widgets(
		document.querySelector('#clckwrkbdgr-autoidle'),
		rules,
	);
}

/** Saves data string to a file.
 */
clckwrkbdgr.autoidle._save_file = function(data, filename)
{
	var a = document.createElement("a");
	var blob = new Blob([data], {type: "octet/stream"});
	var url = window.URL.createObjectURL(blob);
	a.href = url;
	a.download = filename;
	a.click();
	window.URL.revokeObjectURL(url);
	a.remove();
}

/** Open file (using file dialog), reads content and passes to the handler.
 */
clckwrkbdgr.autoidle._open_file = function(handler)
{
	var input = document.createElement('input');
	input.type = 'file';
	input.onchange = e => { 
		var file = e.target.files[0]; 
		var reader = new FileReader();
		reader.readAsText(file, 'UTF-8');
		reader.onload = readerEvent => {
			handler(readerEvent.target.result);
		}
	}
	input.click();
	input.remove();
}

/** Re-creates trigger row.
 * Clears param controls if trigger is without params.
 * Re-creates param controls if trigger have params.
 * If trigger_name is null, searches for the select control
 * to get actual value (useful for onchange event).
 */
clckwrkbdgr.autoidle._update_trigger_param_row = function(parent_element, index, trigger_name, compare_function, compare_value)
{
	var compare_id = 'clckwrkbdgr-auto-trigger-compare-' + index;
	var value_input_id = 'clckwrkbdgr-auto-trigger-value-' + index;

	// First remove compare+value elements, if any.
	var compare_element = document.querySelector('#' + compare_id);
	if(compare_element) {
		compare_element.remove();
	}
	var value_element = document.querySelector('#' + value_input_id);
	if(value_element) {
		value_element.remove();
	}

	// Trigger name is specified only for the first time trigger row
	// is created, taken from the original rule data.
	// On subsequent updates it should be taken from the new, changed value.
	if(trigger_name == null) {
		var trigger_id = 'clckwrkbdgr-auto-trigger-' + index;
		var trigger_element = document.querySelector('#' + trigger_id);
		trigger_name = trigger_element.value;
	}
	var trigger_data = clckwrkbdgr.autoidle._triggers_registry[trigger_name];
	// No params - we're good: name is already changed and compare+value were removed.
	if(!trigger_data.param_type) {
		return;
	}

	// Recreate compare box using param type DB.
	var compare_box = document.createElement('select');
	compare_box.classList.add('clckwrkbdgr-trigger-compare-function');
	compare_box.setAttribute('id', compare_id);
	compare_box.setAttribute('name', compare_id);
	var compare_options = SUPPORTED_PARAM_TYPES[trigger_data.param_type].functions;
	for(var compare_name in compare_options) {
		var compare_option = document.createElement('option');
		compare_option.setAttribute('value', compare_name);
		compare_option.innerText = compare_name;
		compare_box.appendChild(compare_option);
	}
	compare_box.value = compare_function;
	parent_element.appendChild(compare_box);

	// Recreate value input control using param type DB.
	var value_input = document.createElement('input');
	value_input.classList.add('clckwrkbdgr-trigger-value');
	value_input.setAttribute('id', value_input_id);
	value_input.setAttribute('name', value_input_id);
	if(trigger_data.param_type == "number") {
		value_input.setAttribute('type', 'number');
		value_input.setAttribute('value', '0');
		value_input.setAttribute('step', 'any');
		value_input.setAttribute('min', '-999999999');
		value_input.setAttribute('max', '999999999');
	} else {
		value_input.setAttribute('type', 'text');
	}
	value_input.value = compare_value;
	parent_element.appendChild(value_input);
}

/** Removes trigger row for a rule div.
 */
clckwrkbdgr.autoidle._remove_trigger_param_row = function(row_element)
{
	var when_div = row_element.parentElement;
	row_element.remove();

	// If after removing there will remain only one trigger row,
	// it can't be removed.
	var other_rows = when_div.querySelectorAll('a.clckwrkbdgr-remove-trigger-row');
	if(other_rows.length == 1) {
		other_rows[0].style.display = 'none';
	}
}

/** Adds new trigger row.
 * i - rule index;
 * j - trigger index;
 */
clckwrkbdgr.autoidle._add_trigger_row = function(container, trigger, i, j, total_triggers)
{
	// When creating new trigger row, pick some default trigger.
	if(trigger == null) {
		trigger = Object.keys(clckwrkbdgr.autoidle._triggers_registry)[0];
	}
	if(total_triggers == null) {
		var existing_rows = container.querySelectorAll('div.clckwrkbdgr-auto-trigger-row');
		total_triggers = existing_rows.length + 1;
	}
	if(j == null) {
		j = 1;
		var existing_rows = container.querySelectorAll('div.clckwrkbdgr-auto-trigger-row');
		for(var _j = 0; _j < existing_rows.length; ++_j) {
			var when_row = existing_rows[_j];
			var row_j = +(when_row.style['grid-row']);
			j = Math.max(j, row_j);
		}
	}

	var trigger_id = 'clckwrkbdgr-auto-trigger-' + i + '-' + j;

	var when_row = document.createElement('div');
	when_row.classList.add('clckwrkbdgr-auto-trigger-row');
	when_row.style['grid-row'] = j + 1;

	// Button to remove trigger (if there are more than 1).
	var trigger_remove = document.createElement('a');
	trigger_remove.classList.add('clckwrkbdgr-remove-trigger-row');
	trigger_remove.addEventListener("click",
		clckwrkbdgr.autoidle._remove_trigger_param_row.bind(
			null,
			when_row, i + '-' + j,
		),
	);
	trigger_remove.innerText = '[-]';
	when_row.appendChild(trigger_remove);
	if(total_triggers <= 1) {
		trigger_remove.style.display = 'none';
	}

	var trigger_name = Array.isArray(trigger) ? trigger[0] : trigger;

	var trigger_box = document.createElement('select');
	trigger_box.classList.add('clckwrkbdgr-trigger-name');
	trigger_box.setAttribute('id', trigger_id);
	trigger_box.setAttribute('name', trigger_id);
	for(var trigger_opt_name in clckwrkbdgr.autoidle._triggers_registry) {
		var trigger_option = document.createElement('option');
		trigger_option.setAttribute('value', trigger_opt_name);
		trigger_option.innerText = trigger_opt_name;
		trigger_box.appendChild(trigger_option);
	}
	// When new trigger is selected, recreate param row.
	trigger_box.addEventListener("change",
		clckwrkbdgr.autoidle._update_trigger_param_row.bind(
			null,
			when_row, i + '-' + j,
			null,
			Array.isArray(trigger) ? trigger[1] : null,
			Array.isArray(trigger) ? trigger[2] : null,
			)
	);
	trigger_box.value = trigger_name;
	when_row.appendChild(trigger_box);

	// Create param row from initial data.
	clckwrkbdgr.autoidle._update_trigger_param_row(
		when_row, i + '-' + j,
		trigger_name,
		Array.isArray(trigger) ? trigger[1] : null,
		Array.isArray(trigger) ? trigger[2] : null,
		)

	container.appendChild(when_row);

	// If after adding there will be more than one trigger row,
	// they all can be removed now.
	if(total_triggers > 1) {
		var other_rows = container.querySelectorAll('a.clckwrkbdgr-remove-trigger-row');
		for(var _j = 0; _j < other_rows.length; ++_j) {
			other_rows[_j].style.display = 'inline';
		}
	}
}

/** Re-creates param fields for action.
 * Clears param controls if action is without params.
 * Re-creates param controls if action have params.
 * If action_name is null, searches for the select control
 * to get actual value (useful for onchange event).
 */
clckwrkbdgr.autoidle._update_rule_params = function(parent_element, index, action_name, action_parameters)
{
	// First remove previous param fields, if any.
	var fields = parent_element.querySelectorAll('input.clckwrkbdgr-rule-parameter');
	for(var i = 0; i < fields.length; ++i) {
		fields[i].remove();
	}

	// Action name is specified only for the first time action row
	// is created, taken from the original rule data.
	// On subsequent updates it should be taken from the new, changed value.
	if(action_name == null) {
		var action_id = 'clckwrkbdgr-auto-action-' + index;
		var action_element = document.querySelector('#' + action_id);
		action_name = action_element.value;
	}
	var action_data = clckwrkbdgr.autoidle._actions_registry[action_name];
	// No params - we're good: name is already changed and previous fields were removed.
	if(!(action_data.parameters && action_data.parameters.length)) {
		return;
	}

	// Recreate compare box using param type DB.
	for(var j = 0; j < action_data.parameters.length; ++j) {
		var param = action_data.parameters[j];
		var param_input_id = 'clckwrkbdgr-auto-rule-param-' + index + '-' + j;
		var param_input = document.createElement('input');
		param_input.classList.add('clckwrkbdgr-rule-parameter');
		param_input.setAttribute('id', param_input_id);
		param_input.setAttribute('name', param_input_id);
		param_input.setAttribute('type', 'text');
		if(j < action_parameters.length) {
			param_input.value = action_parameters[j];
		}
		parent_element.appendChild(param_input);
	}
}

/** Removes rule row completely.
 */
clckwrkbdgr.autoidle._remove_rule_row = function(row)
{
	row.remove();
}

/** Adds new rule row.
 * If rule is null, picks some default trigger and some default action.
 */
clckwrkbdgr.autoidle._add_new_rule_row = function(container, rule, i)
{
	if(rule == null) {
		rule = {
			enabled: false,
			triggers: [
				Object.keys(clckwrkbdgr.autoidle._triggers_registry)[0],
			],
			action:
				Object.keys(clckwrkbdgr.autoidle._actions_registry)[0],
		};
	}
	if(i == null) {
		i = -1;
		var all_rules = container.querySelectorAll('div.clckwrkbdgr-rule');
		for(var j = 0; j < all_rules.length; ++j) {
			var rule_div = all_rules[j];
			var current_index = +(rule_div.getAttribute('data-rule-index'));
			i = Math.max(i, current_index);
		}
		++i;
	}

	// Main rule container.
	var rule_div = document.createElement('div');
	rule_div.classList.add('clckwrkbdgr-rule');
	rule_div.setAttribute('data-rule-index', i);
	rule_div.style.display = 'grid';
	rule_div.style['grid-template-columns'] = '3em 50% 50%';
	rule_div.style.padding = '10px';
	rule_div.style.border = '1px dashed yellow';

	// If initial rule set is already created and we have meta row,
	// we should add new row before the meta row.
	var rule_meta_div = container.querySelector('div.clckwrkbdgr-rule-meta-row');
	if(rule_meta_div) {
		container.insertBefore(rule_div, rule_meta_div);
	} else {
		container.appendChild(rule_div);
	}

	// Controls for rule management.
	var rule_control_div = document.createElement('div');
	rule_control_div.style['grid-column'] = '1';

	var rule_enabled = document.createElement('input');
	rule_enabled.setAttribute('type', 'checkbox');
	rule_enabled.setAttribute('id', 'clckwrkbdgr-autoidle-enable-rule-' + i);
	rule_enabled.setAttribute('name', 'clckwrkbdgr-autoidle-enable-rule-' + i);
	rule_enabled.checked = !!rule.enabled;
	rule_control_div.appendChild(rule_enabled);

	var rule_remove = document.createElement('a');
	rule_remove.classList.add('clckwrkbdgr-remove-rule');
	rule_remove.addEventListener("click",
		clckwrkbdgr.autoidle._remove_rule_row.bind(
			null,
			rule_div,
		),
	);
	rule_remove.innerText = '[-]';
	rule_control_div.appendChild(rule_remove);

	rule_div.appendChild(rule_control_div);

	// Container for triggers.
	var when_div = document.createElement('div');
	when_div.style['grid-column'] = '2';
	when_div.style.display = 'grid';
	for(var j = 0; j < rule.triggers.length; ++j) {
		var trigger = rule.triggers[j];

		clckwrkbdgr.autoidle._add_trigger_row(
			when_div, trigger, i, j,
			rule.triggers.length,
		);

		if(j == rule.triggers.length - 1) {
			var when_meta_row = document.createElement('div');
			when_meta_row.style['grid-row'] = 999999;
			var trigger_add = document.createElement('a');
			trigger_add.classList.add('clckwrkbdgr-add-trigger-row');
			trigger_add.addEventListener("click",
				clckwrkbdgr.autoidle._add_trigger_row.bind(
					null,
					when_div, null, i, null,
					null,
				),
			);
			trigger_add.innerText = '[+]';
			when_meta_row.appendChild(trigger_add);
			when_div.appendChild(when_meta_row);
		}
	}
	rule_div.appendChild(when_div);

	// Container for action.
	var action_name = Array.isArray(rule.action) ? rule.action[0] : rule.action;
	var action_parameters = Array.isArray(rule.action) ? rule.action.slice(1) : [];

	var do_div = document.createElement('div');
	do_div.style['grid-column'] = '3';
	var action_id = 'clckwrkbdgr-auto-action-' + i;

	var action_label = document.createElement('label');
	action_label.setAttribute('for', action_id);
	action_label.innerText = '=>';
	do_div.appendChild(action_label);

	var action_box = document.createElement('select');
	action_box.classList.add('clckwrkbdgr-rule-action');
	action_box.setAttribute('id', action_id);
	action_box.setAttribute('name', action_id);
	for(var _action_name in clckwrkbdgr.autoidle._actions_registry) {
		var action_option = document.createElement('option');
		action_option.setAttribute('value', _action_name);
		action_option.innerText = _action_name;
		action_box.appendChild(action_option);
	}
	action_box.value = action_name;
	do_div.appendChild(action_box);

	// When new action is selected, recreate param fields.
	action_box.addEventListener("change",
		clckwrkbdgr.autoidle._update_rule_params.bind(
			null,
			do_div, i,
			null,
			action_parameters,
			)
	);

	// Initial parameter fields.
	clckwrkbdgr.autoidle._update_rule_params(
		do_div, i,
		action_name,
		action_parameters,
	);

	rule_div.appendChild(do_div);
}

/** Creates control widgets for rules in given container element.
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._fill_rules_widgets = function(container, rules)
{
	// Clear previous content.
	while(container.firstChild){
		container.removeChild(container.firstChild);
	}

	// Main set of rules.
	for(var i = 0; i < rules.length; ++i) {
		var rule = rules[i];
		clckwrkbdgr.autoidle._add_new_rule_row(container, rule, i);
	}

	// Buttons to control rules (add new rule etc).
	var rule_meta_div = document.createElement('div');
	rule_meta_div.classList.add('clckwrkbdgr-rule-meta-row');
	var rule_add = document.createElement('a');
	rule_add.classList.add('clckwrkbdgr-add-rule');
	rule_add.addEventListener("click",
		clckwrkbdgr.autoidle._add_new_rule_row.bind(
			null,
			container, null, null,
		),
	);
	rule_add.innerText = '[+]';
	rule_meta_div.appendChild(rule_add);
	container.appendChild(rule_meta_div);
}

/** Saves settings from opened dialog.
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._save_settings = function()
{
	// Save 'Enable all' checkbox.
	var autoidle_window_enable_all = document.querySelector('#clckwrkbdgr-autoidle-enable-all');
	if(clckwrkbdgr.autoidle._enable_all != autoidle_window_enable_all.checked) {
		trace(autoidle_window_enable_all.checked ? "Enabling all settings" : "Disabling all settings");
	}
	clckwrkbdgr.autoidle._enable_all = autoidle_window_enable_all.checked;
	clckwrkbdgr.storage.set('clckwrkbdgr-rules-enabled', clckwrkbdgr.autoidle._enable_all);

	// Save changes in rules.
	clckwrkbdgr.autoidle._rules = clckwrkbdgr.autoidle._export_settings();
	trace('Saving rules to local storage...');
	clckwrkbdgr.storage.set('clckwrkbdgr-rules', JSON.stringify(clckwrkbdgr.autoidle._rules));

	// Adjust the text on the main AutoIdle button considering enabled-all state.
	var autoidle_state = document.querySelector('span#clckwrkbdgr-autoidle-state');
	if(!clckwrkbdgr.autoidle._enable_all) {
		autoidle_state.innerText = '(off)';
	} else {
		autoidle_state.innerText = '';
	}
}

/** Closes opened settings dialog.
 * If save == True, saves changes. Default is False (cancel the changes).
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._close_settings = function(save)
{
	// User-defined action.
	if(clckwrkbdgr.autoidle._on_close_settings) {
		try {
			clckwrkbdgr.autoidle._on_close_settings();
		} catch(e) {
			console.error(e);
		}
	}

	// Save and close.
	if(save) {
		clckwrkbdgr.autoidle._save_settings();
	}
	var autoidle_modal_div = document.querySelector('#clckwrkbdgr-autoidle-modal');
	autoidle_modal_div.style.display = 'none';
}

/** Installs AutoIdle handlers.
 *
 * Required parameters:
 * - parent_div_selector - query selector for the element where AutoIdle button will be appended.
 *
 * Optional parameters (last parameter, as dict, can be omitted):
 * - settings_button_name = 'AutoIdle'; // Name of the AutoIdle button that opens settings dialog.
 * - tick_timeout = 1000; // Timeout between rule ticks.
 * - webworker = false; // By default (false) uses direct JS setInterval to check rules,
 *                      // which may fall victim to event throttling when browser tab goes into background.
 *                      // Set to true to use Web Working API, which allows running checks at exact intervals,
 *                      // but may use more resources (memory+CPU).
 * - delay_start = <immediately>; // Function that accepts callback (which starts main loop) and should call it when game is fully loaded.
 *                                // Simplified example: function(callback) { setTimeout(callback, 1000); } // Start in 1 sec after page is loaded.
 * - on_open: function() // Function to call before settings dialog is opened.
 * - on_close: function() // Function to call before settings dialog is closed (by either OK or Cancel).
 */
clckwrkbdgr.autoidle.install = function(parent_div_selector, _options)
{
	if(!_options) {
		_options = {};
	}

	// Custom events.
	if(_options.on_open) {
		clckwrkbdgr.autoidle._on_open_settings = _options.on_open;
	}
	if(_options.on_close) {
		clckwrkbdgr.autoidle._on_close_settings = _options.on_close;
	}

	// Creating main button.
	var autoidle_button = document.createElement('a');
	autoidle_button.innerText = _options.settings_button_name || 'AutoIdle';
	autoidle_button.setAttribute('onclick', 'clckwrkbdgr.autoidle.open_settings(); return false;');
	var autoidle_state = document.createElement('span');
	autoidle_state.setAttribute('id', 'clckwrkbdgr-autoidle-state');
	autoidle_button.appendChild(autoidle_state);

	// Placing it.
	var parent_div = document.querySelector(parent_div_selector);
	parent_div.appendChild(autoidle_button);

	// Starting actual loop.
	var config = clckwrkbdgr.autoidle._config;
	config.tick_timeout = _options.tick_timeout || 1000;
	var delay_start = _options.delay_start || function(callback) { callback(); };
	if(_options.webworker) {
		var blob = new Blob([
			"onmessage = function(e) { setInterval(function(){ postMessage('tick'); }, " + config.tick_timeout + "); }",
		]);
		var blobURL = window.URL.createObjectURL(blob);

		config.worker = new Worker(blobURL);
		config.worker.addEventListener("message", function(e) {
			clckwrkbdgr.autoidle._check_rules();
		});
		delay_start(function() {
			config.worker.postMessage("tick");
		});
	} else {
		delay_start(function() {
			config.timer = setInterval(clckwrkbdgr.autoidle._check_rules, config.tick_timeout);
		});
	}
}

/// ENGINE /////////////////////////////////////////////////////////////////////

var trace = clckwrkbdgr.tracer('autoidle');

/** Register custom watcher.
 * Watcher tracks value (the result of the given callable)
 * via clckwrkbdgr.autoidle.watcher_changed(name).
 * The result of the watcher_changed will be valid for the whole rule check run.
 * Name could be any form of ID, it is internal only and not visible on any form.
 * Can be used in triggers:
 *   setup_trigger("Value changed", function() {
 *     return clckwrkbdgr.autoidle.watcher_changed('my_watcher');
 *   });
 */
clckwrkbdgr.autoidle.setup_watcher = function(name, callable,
	_options)
{
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	autoidle._watchers_registry[name] = callable;
	trace('Registered watcher "' + name + '".');
}

var SUPPORTED_PARAM_TYPES = {
	"number" : {
		"functions" : {
			"==" : function(a, b) { return (+a) == (+b); },
			"!=" : function(a, b) { return (+a) != (+b); },
			"<=" : function(a, b) { return (+a) <= (+b); },
			">=" : function(a, b) { return (+a) >= (+b); },
			"<" : function(a, b) { return (+a) < (+b); },
			">" : function(a, b) { return (+a) > (+b); },
		}
	},
	"string" : {
		"functions" : {
			"equal" : function(a, b) { return (""+a) == (""+b); },
			"not-equal" : function(a, b) { return (""+a) != (""+b); },
			"==" : function(a, b) { return (""+a) == (""+b); },
			"!=" : function(a, b) { return (""+a) != (""+b); },
		}
	}
};

/** Setup trigger.
 * Assigns name to a callable object (no parameters, should return value).
 *
 * Has two forms:
 * - (name, callable[, _options])
 *   Uncoditional trigger. Callable should return bool (triggered or not).
 * - (name, callable, param_type[, _options])
 *   Conditional trigger based on target value. Callable should return value of specified type.
 *   Trigger is activated when comparison function successfully checks value returned by callable against the target value.
 *   Such triggers should have additional params in a rule:
 *     [trigger_name, param_compare_function, param_target_value]
 *   
 * Supported param types and comparison functions:
 * - "string":
 *   "equal", "not-equal", "==", "!=".
 * - "number" (both integer and float):
 *   "==", "!=", ">=", "<=", ">", "<".
 * This name can be later reused in add_rule.
 */
clckwrkbdgr.autoidle.setup_trigger = function(name, callable,
	param_type,
	_options)
{
	if(is_dict(param_type)) {
		if(!(_options == undefined)) {
			console.error("Param type cannot be dict!");
			return false;
		}
		_options = param_type;
		param_type = undefined;
	}
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	var trigger = {
		"name" : name,
		"callable" : callable,
	};
	if(param_type) {
		if(SUPPORTED_PARAM_TYPES[param_type] == undefined) {
			console.error("Param type is unknown: " + param_type);
			return false;
		}
		trigger["param_type"] = param_type;
	}
	autoidle._triggers_registry[name] = trigger;
	trace('Registered trigger "' + name + '": ' + JSON.stringify(trigger));
}

/** Setup action.
 * Assigns name to a callable object (no parameters, should return bool).
 * This name can be later reused in add_rule.
 * Optional parameter list can be set for the rule - specific rule
 * should define values for these parameters to be passed to the callable.
 * NOTE: resulting parameters of the callable may lose type and be strings or even undefined, so callable should be aware of that.
 */
clckwrkbdgr.autoidle.setup_action = function(name, callable, parameters,
	_options)
{
	if(is_dict(parameters)) {
		if(!(_options == undefined)) {
			console.error("Parameter list cannot be dict!");
			return false;
		}
		_options = parameters;
		parameters = undefined;
	}
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	var action = {
		"name" : name,
		"callable" : callable,
		"parameters" : parameters,
	};
	autoidle._actions_registry[name] = action;
	trace('Registered action "' + name + '": ' + JSON.stringify(action));
}

/** Manually add rule.
 * Rules consists of triggers and action - names in corresponding registries.
 * Trigger function should return True if check is successful and action should be performed.
 * Optional parameter 'disabled' can be set to True to disable rule by default
 * (it will need to be enabled manually later).
 */
clckwrkbdgr.autoidle.add_rule = function(triggers, action, _options)
{
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	var rule = {
		"triggers" : triggers,
		"action" : action,
		"enabled" : !_options.disabled,
	};
	autoidle._rules.push(rule);
	trace('Added rule: ' + JSON.stringify(rule));
}

clckwrkbdgr.autoidle.watcher_changed = function(name, _options)
{
	trace('Checking watcher: ' + name);
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	if(autoidle._watchers_changed[name]) {
		trace('  Watched is considered changed for this run.');
		return true;
	}
	trace('  Watched was not changed.');
	return false;
}

clckwrkbdgr.autoidle._check_trigger = function(trigger, compare_function, target_value)
{
	trace('Checking trigger: ' + JSON.stringify(trigger));
	if(trigger.param_type) {
		var current_value = trigger.callable();
		trace('  Comparing current (' + current_value + ') with target (' + target_value + ')');
		if(compare_function(current_value, target_value)) {
			trace('    Match.');
			return true;
		}
		trace('    Do not match.');
		return false;
	}
	trace('  Calling for bool callable.');
	if(trigger.callable()) {
		trace('    Triggered (true).');
		return true;
	}
	trace('    Did not trigger (false).');
	return false;
}

/** Performs main autoidle process: single run for all rules.
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._check_rules = function(_options)
{
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	if(!autoidle._enable_all) {
		trace('Autoidle disabled.');
		return;
	}

	trace('Updating ' + Object.keys(autoidle._watchers_registry).length + ' watchers...');
	autoidle._watchers_changed = {};
	for(var watcher_name in autoidle._watchers_registry) {
		trace('Updating watcher: ' + watcher_name);
		var new_value = undefined;
		try {
			new_value = autoidle._watchers_registry[watcher_name]();
			trace('  New value: ' + JSON.stringify([new_value]));
		} catch(e) {
			console.error(e);
			continue
		}
		if(autoidle._watchers[watcher_name] == undefined) {
			autoidle._watchers[watcher_name] = new_value;
			trace("  Brand new value. Considering not changed yet.");
		} else if(autoidle._watchers[watcher_name] != new_value) {
			trace("  Value is changed, was: " + JSON.stringify([
				autoidle._watchers[watcher_name],
			]));
			autoidle._watchers[watcher_name] = new_value;
			autoidle._watchers_changed[watcher_name] = true;
		} else {
			trace("  Value was not changed.");
		}
	}

	trace('Checking ' + autoidle._rules.length + ' rules...');
	for(var i = 0; i < autoidle._rules.length; ++i) {
		var rule = autoidle._rules[i];
		trace('Checking rule: ' + JSON.stringify(rule));

		if(!rule.enabled) {
			trace('  Rule is disabled, skipping.');
			continue;
		}

		// Rule is triggered only if all triggers are ON.
		var triggered = true;
		for(var j = 0; j < rule.triggers.length; ++j) {
			var trigger_name = rule.triggers[j]
			var param_compare_function = undefined;
			var param_target_value = undefined;
			if(Array.isArray(trigger_name)) {
				if(trigger_name.length != 3) {
					console.error("Expected 3 values in parametrized trigger, got " + trigger_name.length + ": " + trigger_name);
					triggered = false;
					break;
				}
				param_compare_function = trigger_name[1];
				param_target_value = trigger_name[2];
				trigger_name = trigger_name[0];
			}

			var trigger = autoidle._triggers_registry[trigger_name];
			if(!trigger) {
				console.error("Trigger is undefined: " + trigger_name);
				triggered = false;
				break;
			}

			var param_type = trigger.param_type;
			if(param_compare_function) {
				if(SUPPORTED_PARAM_TYPES[param_type].functions[param_compare_function] == undefined) {
					console.error("Param comparison function is unknown for type " + param_type + ": " + param_compare_function);
					triggered = false;
					break;
				}
				param_compare_function = SUPPORTED_PARAM_TYPES[trigger.param_type].functions[param_compare_function];
			}

			try {
				if(!clckwrkbdgr.autoidle._check_trigger(trigger, param_compare_function, param_target_value)) {
					triggered = false;
					break;
				}
			} catch(e) {
				console.error(e);
				triggered = false;
				break;
			}
		}
		if(!triggered) {
			trace('  Did not trigger.');
			continue;
		}
		trace('  Triggered.');

		// Perform action.
		var action_name = Array.isArray(rule.action) ? rule.action[0] : rule.action;
		var action_parameters = Array.isArray(rule.action) ? rule.action.slice(1) : [];
		var action = autoidle._actions_registry[action_name];
		if(!action) {
			console.error("Action is undefined: " + action_name);
			continue;
		}
		try{
			if(action_parameters.length) {
				trace("  With parameters: " + JSON.stringify(action_parameters));
				action.callable(...action_parameters);
			} else {
				action.callable();
			}
			trace('  Performed action.');
		} catch(e) {
			console.error(e);
		}
	}
}

/** Tries to load rule set from local storage.
 * Returns True on success, False if there were no rules stored.
 */
clckwrkbdgr.autoidle.load_from_storage = function()
{
	trace('Loading rules from local storage...');

	clckwrkbdgr.autoidle._enable_all = clckwrkbdgr.storage.get('clckwrkbdgr-rules-enabled', 'true') == 'true';
	var autoidle_state = document.querySelector('span#clckwrkbdgr-autoidle-state');
	if(!clckwrkbdgr.autoidle._enable_all) {
		trace('  Rules were disabled.');
		autoidle_state.innerText = '(off)';
	} else {
		trace('  Rules were enabled.');
		autoidle_state.innerText = '';
	}

	var stored_rules = clckwrkbdgr.storage.get('clckwrkbdgr-rules', '');
	if(!stored_rules) {
		trace('  No rules were stored.');
		return false;
	}
	try {
		clckwrkbdgr.autoidle._rules = JSON.parse(stored_rules);
		for(var i = 0; i < clckwrkbdgr.autoidle._rules.length; ++i) {
			if(clckwrkbdgr.autoidle._rules[i].enabled == undefined) {
				clckwrkbdgr.autoidle._rules[i].enabled = false;
			}
		}
	} catch(e) {
		console.error(e);
		clckwrkbdgr.autoidle._rules = [];
	}
	trace('  Loaded ' + clckwrkbdgr.autoidle._rules.length + ' rules.');
	return true;
}


/* Example:

clckwrkbdgr.autoidle.install('.navbar-header', {
	delay_start: function(callback) { setTimeout(callback, 1000); },
});

clckwrkbdgr.autoidle.setup_watcher("current_zone", function() { return game.global.world; });

clckwrkbdgr.autoidle.setup_trigger("Always", function() { return true; });
clckwrkbdgr.autoidle.setup_trigger("Storage is full", function() { return Game.storage.value == Game.storage.maxValue; });
clckwrkbdgr.autoidle.setup_trigger("Resource amount %", function() { return Game.resource.amount; }, "number");
clckwrkbdgr.autoidle.setup_trigger("New zone", function() {
	return clckwrkbdgr.autoidle.watcher_changed('current_zone');
});

clckwrkbdgr.autoidle.setup_action("Praise the sun", praise_the_sun);
clckwrkbdgr.autoidle.setup_action("Buy storage", autobuy_storage);
clckwrkbdgr.autoidle.setup_action("Notify", show_notification, ["message"]);

if(!clckwrkbdgr.autoidle.load_from_storage()) {
	clckwrkbdgr.autoidle.add_rule(["Always"], "Praise the sun", {disabled:true});
	clckwrkbdgr.autoidle.add_rule([
		"Storage is full",
		["Resource amount %", ">=", 95],
		], "Buy storage");
	clckwrkbdgr.autoidle.add_rule(["Storage is full"], ["Notify", "Storage is full"]);
}

*/

////////////////////////////////////////////////////////////////////////////////
clckwrkbdgr.export_object(clckwrkbdgr, 'clckwrkbdgr');
