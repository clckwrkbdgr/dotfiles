// Library for creation (mostly injection) of simple UI.
// All functions/classes are available under namespace clckwrkbdgr.autoidle.*

// TODO requires ./utils.js

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};
if(!window.clckwrkbdgr['autoidle']) window.clckwrkbdgr.autoidle = {};

function is_dict(value)
{
	return value && value.constructor == Object;
}

var trace = clckwrkbdgr.tracer('autoidle');

clckwrkbdgr.autoidle = {};
clckwrkbdgr.autoidle._enable_all = true;
clckwrkbdgr.autoidle._triggers_registry = {};
clckwrkbdgr.autoidle._actions_registry = {};
clckwrkbdgr.autoidle._rules = [];

/// GUI ////////////////////////////////////////////////////////////////////////

/** Creates modal settings dialog.
 */
clckwrkbdgr.autoidle._create_settings_modal = function()
{
	// Main background div.
	var autoidle_modal_div = document.createElement('div');
	autoidle_modal_div.setAttribute('id', 'clckwrkbdgr-autoidle-modal');
	autoidle_modal_div.style.display = 'none';
	autoidle_modal_div.style.position = "fixed";
	autoidle_modal_div.style['z-index'] = "1";
	autoidle_modal_div.style.left = "0px";
	autoidle_modal_div.style.top = "0px";
	autoidle_modal_div.style.width = "96%";
	autoidle_modal_div.style.height = "96%";
	autoidle_modal_div.style['background-color'] = "rgba(0, 0, 0, 0.5)";

	// Main dialog window.
	var autoidle_window = document.createElement('div');
	autoidle_window.style.margin = "2%";
	autoidle_window.style['background-color'] = "#333";
	autoidle_window.style.padding = "10px";
	autoidle_window.style.border = "1px solid yellow";
	autoidle_window.style.width = "96%";
	autoidle_window.style.height = "94%";

	// Window header.
	var autoidle_window_header = document.createElement('ul');
	autoidle_window_header.style.padding = "10px";
	autoidle_window_header.style.display = "flex";
	autoidle_window_header.style.width = '98%';
	autoidle_window_header.style['border-bottom'] = '1px solid yellow';
	autoidle_window.appendChild(autoidle_window_header);

	// Window title and place for control buttons.
	var autoidle_window_title = document.createElement('p');
	autoidle_window_title.innerText = 'AutoIdle';
	var autoidle_window_title_li = document.createElement('li');
	autoidle_window_title_li.style.display = "flex";
	autoidle_window_title_li.style.width = "98%";
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
	autoidle_window_main_settings.style.width = '98%';
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

	// Main working area.
	var autoidle_content = document.createElement('div');
	autoidle_content.setAttribute('id', 'clckwrkbdgr-autoidle');
	autoidle_content.style.margin = "5%";
	autoidle_content.style.width = "90%";
	autoidle_content.style.height = "90%";
	autoidle_content.style.overflow = "auto";
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
	// Find or create modal dialog.
	var autoidle_modal_div = document.querySelector('#clckwrkbdgr-autoidle-modal');
	if(!autoidle_modal_div) {
		autoidle_modal_div = clckwrkbdgr.autoidle._create_settings_modal();
	}

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

/** Creates control widgets for rules in given container element.
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._fill_rules_widgets = function(container, rules)
{
	for(var i = 0; i < rules.length; ++i) {
		var rule = rules[i];
		var rule_div = document.createElement('div');
		rule_div.style.display = 'grid';
		rule_div.style.padding = '10px';
		rule_div.style.border = '1px dashed yellow';

		var when_div = document.createElement('div');
		when_div.style['grid-column'] = '1';
		for(var j = 0; j < rule.triggers.length; ++j) {
			var trigger = rule.triggers[j];
			var trigger_id = 'clckwrkbdgr-auto-trigger-' + i + '-' + j;

			var trigger_label = document.createElement('label');
			trigger_label.setAttribute('for', trigger_id);
			trigger_label.innerText = j == 0 ? 'When' : 'and';
			when_div.appendChild(trigger_label);

			var trigger_name = Array.isArray(trigger) ? trigger[0] : trigger;

			var trigger_box = document.createElement('select');
			trigger_box.setAttribute('id', trigger_id);
			trigger_box.setAttribute('name', trigger_id);
			for(var trigger_opt_name in clckwrkbdgr.autoidle._triggers_registry) {
				var trigger_option = document.createElement('option');
				trigger_option.setAttribute('value', trigger_opt_name);
				trigger_option.innerText = trigger_opt_name;
				trigger_box.appendChild(trigger_option);
			}
			trigger_box.value = trigger_name;
			when_div.appendChild(trigger_box);

			if(Array.isArray(trigger)) {
				var trigger_data = clckwrkbdgr.autoidle._triggers_registry[trigger_name];
				var compare_function = trigger[1];
				var compare_box = document.createElement('select');
				var compare_id = 'clckwrkbdgr-auto-trigger-compare-' + i + '-' + j;
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
				when_div.appendChild(compare_box);

				var compare_value = trigger[2];
				var value_input_id = 'clckwrkbdgr-auto-trigger-value-' + i + '-' + j;
				var value_input = document.createElement('input');
				value_input.setAttribute('id', value_input_id);
				value_input.setAttribute('name', value_input_id);
				if(trigger_data.param_type == "number") {
					value_input.setAttribute('type', 'number');
					value_input.setAttribute('value', '0');
					value_input.setAttribute('min', '-999999999');
					value_input.setAttribute('max', '999999999');
				} else {
					value_input.setAttribute('type', 'text');
				}
				value_input.value = compare_value;
				when_div.appendChild(value_input);
			}
		}
		rule_div.appendChild(when_div);

		var do_div = document.createElement('div');
		do_div.style['grid-column'] = '2';
		var action_id = 'clckwrkbdgr-auto-action-' + i;
		var action_label = document.createElement('label');
		action_label.setAttribute('for', action_id);
		action_label.innerText = 'Do:';
		var action_box = document.createElement('select');
		action_box.setAttribute('id', action_id);
		action_box.setAttribute('name', action_id);
		for(var action_name in clckwrkbdgr.autoidle._actions_registry) {
			var action_option = document.createElement('option');
			action_option.setAttribute('value', action_name);
			action_option.innerText = action_name;
			action_box.appendChild(action_option);
		}
		action_box.value = rule.action;
		do_div.appendChild(action_label);
		do_div.appendChild(action_box);
		rule_div.appendChild(do_div);

		container.appendChild(rule_div);
	}
}

/** Saves settings from opened dialog.
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._save_settings = function()
{
	// Save 'Enable all' checkbox.
	var autoidle_window_enable_all = document.querySelector('#clckwrkbdgr-autoidle-enable-all');
	if(clckwrkbdgr.autoidle._enable_all != autoidle_window_enable_all.checked) {
		console.log(autoidle_window_enable_all.checked ? "Enabling all settings" : "Disabling all settings");
	}
	clckwrkbdgr.autoidle._enable_all = autoidle_window_enable_all.checked;

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
 * - delay_start = <immediately>; // Function that accepts callback (which starts main loop) and should call it when game is fully loaded.
 *                                // Simplified example: function(callback) { setTimeout(callback, 1000); } // Start in 1 sec after page is loaded.
 */
clckwrkbdgr.autoidle.install = function(parent_div_selector, _options)
{
	if(!_options) {
		_options = {};
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
	var delay_start = _options.delay_start || function(callback) { callback(); };
	delay_start(function() {
		clckwrkbdgr.autoidle._timer = setInterval(clckwrkbdgr.autoidle._check_rules, _options.tick_timeout || 1000);
	});
}

/// ENGINE /////////////////////////////////////////////////////////////////////

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
 * - "number":
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
}

/** Setup action.
 * Assigns name to a callable object (no parameters, should return bool).
 * This name can be later reused in add_rule.
 */
clckwrkbdgr.autoidle.setup_action = function(name, callable, _options)
{
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	var trigger = {
		"name" : name,
		"callable" : callable,
	};
	autoidle._actions_registry[name] = trigger;
}

/** Manually add rule.
 * Rules consists of triggers and action - names in corresponding registries.
 * Trigger function should return True if check is successful and action should be performed.
 */
clckwrkbdgr.autoidle.add_rule = function(triggers, action, _options)
{
	_options = _options || {};
	var autoidle = _options.autoidle || clckwrkbdgr.autoidle;
	var rule = {
		"triggers" : triggers,
		"action" : action,
	};
	autoidle._rules.push(rule);
}

clckwrkbdgr.autoidle._check_trigger = function(trigger, compare_function, target_value)
{
	if(trigger.param_type) {
		var current_value = trigger.callable();
		if(compare_function(current_value, target_value)) {
			return true;
		}
		return false;
	}
	if(trigger.callable()) {
		return true;
	}
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
		return;
	}
	for(var i = 0; i < autoidle._rules.length; ++i) {
		var rule = autoidle._rules[i];

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

			if(!clckwrkbdgr.autoidle._check_trigger(trigger, param_compare_function, param_target_value)) {
				triggered = false;
				break;
			}
		}
		if(!triggered) {
			continue;
		}

		// Perform action.
		var action = autoidle._actions_registry[rule.action];
		if(!action) {
			console.error("Action is undefined: " + rule.action);
			continue;
		}
		action.callable();
	}
}

/* Example:

clckwrkbdgr.autoidle.install('.navbar-header', {
	delay_start: function(callback) { setTimeout(callback, 1000); },
});
clckwrkbdgr.autoidle.setup_trigger("Always", function() { return true; });
clckwrkbdgr.autoidle.setup_trigger("Storage is full", function() { return Game.storage.value == Game.storage.maxValue; });
clckwrkbdgr.autoidle.setup_trigger("Resource amount %", function() { return Game.resource.amount; }, "number");

clckwrkbdgr.autoidle.setup_action("Praise the sun", praise_the_sun);
clckwrkbdgr.autoidle.setup_action("Buy storage", autobuy_storage);

clckwrkbdgr.autoidle.add_rule(["Always"], "Praise the sun");
clckwrkbdgr.autoidle.add_rule([
		"Storage is full",
		["Resource amount %", ">=", 95],
		], "Buy storage");

*/

////////////////////////////////////////////////////////////////////////////////
clckwrkbdgr.export_object(clckwrkbdgr, 'clckwrkbdgr');
