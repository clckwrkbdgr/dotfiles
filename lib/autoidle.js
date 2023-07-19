// Library for creation (mostly injection) of simple UI.
// All functions/classes are available under namespace clckwrkbdgr.autoidle.*

// TODO requires ./utils.js

if(!window['clckwrkbdgr']) window.clckwrkbdgr = {};
if(!window.clckwrkbdgr['autoidle']) window.clckwrkbdgr.autoidle = {};

var trace = clckwrkbdgr.tracer('autoidle');

clckwrkbdgr.autoidle = {};
clckwrkbdgr.autoidle._enable_all = true;
clckwrkbdgr.autoidle._triggers = {};
clckwrkbdgr.autoidle._actions = {};
clckwrkbdgr.autoidle._rules = [];

/** Creates modal settings dialog.
 */
clckwrkbdgr.autoidle._create_settings_modal = function()
{
	var autoidle_modal_div = document.createElement('div');
	autoidle_modal_div.setAttribute('id', 'clckwrkbdgr-autoidle-modal');
	autoidle_modal_div.style.display = 'none';
	autoidle_modal_div.style.position = "fixed";
	autoidle_modal_div.style['z-index'] = "1";
	autoidle_modal_div.style.left = "0px";
	autoidle_modal_div.style.top = "0px";
	autoidle_modal_div.style.width = "100%";
	autoidle_modal_div.style.height = "100%";
	autoidle_modal_div.style['background-color'] = "rgba(0, 0, 0, 0.5)";

	var autoidle_window = document.createElement('div');
	autoidle_window.style.margin = "2%";
	autoidle_window.style['background-color'] = "#333";
	autoidle_window.style.padding = "10px";
	autoidle_window.style.border = "1px solid yellow";
	autoidle_window.style.width = "96%";
	autoidle_window.style.height = "94%";

	var autoidle_window_header = document.createElement('ul');
	autoidle_window_header.style.padding = "10px";
	autoidle_window_header.style.display = "flex";
	autoidle_window_header.style.width = '100%';
	autoidle_window_header.style['border-bottom'] = '1px solid yellow';
	autoidle_window.appendChild(autoidle_window_header);

	var autoidle_window_title = document.createElement('p');
	autoidle_window_title.innerText = 'AutoIdle';
	var autoidle_window_title_li = document.createElement('li');
	autoidle_window_title_li.style.display = "flex";
	autoidle_window_title_li.style.width = "100%";
	autoidle_window_title_li.appendChild(autoidle_window_title);
	autoidle_window_header.appendChild(autoidle_window_title_li);

	var save_autoidle_window = document.createElement('a');
	save_autoidle_window.innerText = 'Save';
	save_autoidle_window.setAttribute('onclick', 'autoidle._close_settings(true); return false;');
	var save_autoidle_window_li = document.createElement('li');
	save_autoidle_window_li.style.display = "flex";
	save_autoidle_window_li.style.border = "1px yellow solid";
	save_autoidle_window_li.style.padding = "5px";
	save_autoidle_window_li.style.margin = "5px";
	save_autoidle_window_li.appendChild(save_autoidle_window);
	autoidle_window_header.appendChild(save_autoidle_window_li);

	var cancel_autoidle_window = document.createElement('a');
	cancel_autoidle_window.innerText = 'Cancel';
	cancel_autoidle_window.setAttribute('onclick', 'autoidle._close_settings(); return false;');
	var cancel_autoidle_window_li = document.createElement('li');
	cancel_autoidle_window_li.style.display = "flex";
	cancel_autoidle_window_li.style.border = "1px yellow solid";
	cancel_autoidle_window_li.style.padding = "5px";
	cancel_autoidle_window_li.style.margin = "5px";
	cancel_autoidle_window_li.appendChild(cancel_autoidle_window);
	autoidle_window_header.appendChild(cancel_autoidle_window_li);

	var autoidle_window_main_settings = document.createElement('ul');
	autoidle_window_main_settings.style.padding = "10px";
	autoidle_window_main_settings.style.display = "flex";
	autoidle_window_main_settings.style.width = '100%';
	autoidle_window_main_settings.style['border-bottom'] = '1px solid yellow';
	autoidle_window.appendChild(autoidle_window_main_settings);

	var autoidle_window_enable_all = document.createElement('input');
	autoidle_window_enable_all.setAttribute('type', 'checkbox');
	autoidle_window_enable_all.setAttribute('id', 'clckwrkbdgr-autoidle-enable-all');
	autoidle_window_enable_all.setAttribute('name', 'clckwrkbdgr-autoidle-enable-all');
	autoidle_window_main_settings.appendChild(autoidle_window_enable_all);

	var autoidle_window_enable_all_label = document.createElement('label');
	autoidle_window_enable_all_label.setAttribute('for', 'clckwrkbdgr-autoidle-enable-all');
	autoidle_window_enable_all_label.innerText = 'Enable all';
	autoidle_window_main_settings.appendChild(autoidle_window_enable_all_label);

	var autoidle_content = document.createElement('div');
	autoidle_content.setAttribute('id', 'clckwrkbdgr-autoidle');
	autoidle_content.style.margin = "5%";
	autoidle_content.style.width = "90%";
	autoidle_content.style.height = "90%";
	autoidle_content.style.overflow = "auto";
	autoidle_window.appendChild(autoidle_content);

	autoidle_modal_div.appendChild(autoidle_window);
	document.body.appendChild(autoidle_modal_div);

	return autoidle_modal_div;
}

/** Opens settings dialog.
 */
clckwrkbdgr.autoidle.open_settings = function()
{
	var autoidle_modal_div = document.querySelector('#clckwrkbdgr-autoidle-modal');
	if(!autoidle_modal_div) {
		autoidle_modal_div = clckwrkbdgr.autoidle._create_settings_modal();
	}

	var autoidle_window_enable_all = document.querySelector('#clckwrkbdgr-autoidle-enable-all');
	autoidle_window_enable_all.checked = clckwrkbdgr.autoidle._enable_all;

	autoidle_modal_div.style.display = 'block';
}

/** Closes opened settings dialog.
 * If save == True, saves changes. Default is False (cancel the changes).
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._close_settings = function(save)
{
	if(save) {
		var autoidle_window_enable_all = document.querySelector('#clckwrkbdgr-autoidle-enable-all');
		if(clckwrkbdgr.autoidle._enable_all != autoidle_window_enable_all.checked) {
			console.log(autoidle_window_enable_all.checked ? "Enabling all settings" : "Disabling all settings");
		}
		clckwrkbdgr.autoidle._enable_all = autoidle_window_enable_all.checked;

		var autoidle_state = document.querySelector('span#clckwrkbdgr-autoidle-state');
		if(!clckwrkbdgr.autoidle._enable_all) {
			autoidle_state.innerText = '(off)';
		} else {
			autoidle_state.innerText = '';
		}
	}
	var autoidle_modal_div = document.querySelector('#clckwrkbdgr-autoidle-modal');
	autoidle_modal_div.style.display = 'none';
}

/** Installs AutoIdle handlers.
 *
 * Required parameters:
 * - parent_div_selector - query selector for the element where AutoIdle button will be appended.
 *
 * Optional parameters (last parameter as dict, can be omitted):
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
	var autoidle_button = document.createElement('a');
	autoidle_button.innerText = _options.settings_button_name || 'AutoIdle';
	autoidle_button.setAttribute('onclick', 'autoidle.open_settings(); return false;');
	var autoidle_state = document.createElement('span');
	autoidle_state.setAttribute('id', 'clckwrkbdgr-autoidle-state');
	autoidle_button.appendChild(autoidle_state);

	var parent_div = document.querySelector(parent_div_selector);
	parent_div.appendChild(autoidle_button);

	var delay_start = _options.delay_start || function(callback) { callback(); };
	delay_start(function() {
		clckwrkbdgr.autoidle._timer = setInterval(clckwrkbdgr.autoidle._check_rules, _options.tick_timeout || 1000);
	});
}

/** Setup trigger.
 * Assigns name to a callable object (no parameters, should return bool).
 * This name can be later reused in add_rule.
 */
clckwrkbdgr.autoidle.setup_trigger = function(name, callable)
{
	var trigger = {
		"name" : name,
		"callable" : callable,
	};
	clckwrkbdgr.autoidle._triggers[name] = trigger;
}

/** Setup action.
 * Assigns name to a callable object (no parameters, should return bool).
 * This name can be later reused in add_rule.
 */
clckwrkbdgr.autoidle.setup_action = function(name, callable)
{
	var trigger = {
		"name" : name,
		"callable" : callable,
	};
	clckwrkbdgr.autoidle._actions[name] = trigger;
}

/** Manually add rule.
 * Rules consists of triggers and action - names in corresponding registries.
 * Trigger function should return True if check is successful and action should be performed.
 */
clckwrkbdgr.autoidle.add_rule = function(triggers, action)
{
	var rule = {
		"triggers" : triggers,
		"action" : action,
	};
	clckwrkbdgr.autoidle._rules.push(rule);
}

/** Performs main autoidle process: single run for all rules.
 * Almost never should be called manually.
 */
clckwrkbdgr.autoidle._check_rules = function()
{
	if(!clckwrkbdgr.autoidle._enable_all) {
		return;
	}
	for(var i = 0; i < clckwrkbdgr.autoidle._rules.length; ++i) {
		var rule = clckwrkbdgr.autoidle._rules[i];
		var triggered = true;
		for(var j = 0; j < rule.triggers.length; ++j) {
			var trigger = clckwrkbdgr.autoidle._triggers[rule.triggers[j]];
			if(!trigger) {
				console.error("Trigger is undefined: " + rule.triggers[j]);
				triggered = false;
				break;
			}
			if(!trigger.callable()) {
				triggered = false;
				break;
			}
		}
		if(!triggered) {
			continue;
		}
		var action = clckwrkbdgr.autoidle._actions[rule.action];
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
clckwrkbdgr.autoidle.setup_action("Buy storage", autobuy_storage);
clckwrkbdgr.autoidle.add_rule(["Always"], "Buy storage");

*/

////////////////////////////////////////////////////////////////////////////////
clckwrkbdgr.export_object(clckwrkbdgr, 'clckwrkbdgr');
