// ==UserScript==
// @name        autoskipper
// @namespace   chatvdvoem
// @include     https://chatvdvoem.ru/*
// @version     1
// @grant       none
// ==/UserScript==
function inject(fn) {
	source = '(' + fn + ')();';

	var script = document.createElement('script');
	script.setAttribute("type", "application/javascript");
	script.textContent = source;
	document.body.appendChild(script);
}

inject(function() {

	function log(msg) {
		if (window.cvtSettings.debugLogging) {
			console.log(msg);
		}
	}

	function injectToFrame(fn, frame) {
		source = fn.toString();

		var script = frame.document.createElement('script');
		script.setAttribute("type", "application/javascript");
		script.textContent = source;
		frame.document.body.appendChild(script);
	}

	if(!('contains' in String.prototype)) {
		String.prototype.contains = function(str, startIndex) {
			return -1 !== String.prototype.indexOf.call(this, str, startIndex);
		};
	}

	window.use_old_design = false;
	var TEST = false;

	// Oldcompat functions.
	function compat_closeCurrentChat() {
		if(window.use_old_design) {
			closeCurrentChat();
		} else {
			chat.close();
		}
	}
	function compat_startNewChat() {
		if(window.use_old_design) {
			startNewChat();
		} else {
			chat.start();
		}
	}
	function compat_sendNewMessage(text) {
		if(window.use_old_design) {
			sendNewMessage();
		} else {
			chat.sendMessage(text);
		}
	}
  
  function restartChat() {
	  compat_closeCurrentChat();
	  setTimeout(compat_startNewChat, 1000);
  }

  var button_close_id = window.use_old_design ? "#chat_close" : "#but-close";

  $(button_close_id).click(function() {
		//load_responses();
    restartChat();
  });

/* Basic responses are now should be loaded from local file.
 * File should contains text lines, each line should represent a valid JS regexp object (e.g.: /hello/i).
 * Each regexp can be followed by an arrow and an answer, enclosed in quotes:
 *    /expr/m   =>   "answer"
 * If answer is an empty string ("" or ''), it does not get posted, but the auto-response mode is still on.
 * Empty lines are ignored.
 * Local storage should be available (set cookies for https://chatvdvoem.ru).
 */

	var RESTART_CHAT_TIMEOUT = '5'; // seconds.
var RESPONSES = [
		[ undefined, [
			/^.$/, /^(.)\\1+$/, /^[0-9]+$/
		]	],
	]

	function notify(text) {
		// Let's check if the browser supports notifications
		if (!("Notification" in window)) {
			console.log("This browser does not support desktop notification");
		}

		// Let's check whether notification permissions have already been granted
		else if (Notification.permission === "granted") {
			// If it's okay let's create a notification
			var notification = new Notification(text);
		}

		// Otherwise, we need to ask the user for permission
		else if (Notification.permission !== "denied") {
			Notification.requestPermission(function (permission) {
				// If the user accepts, let's create a notification
				if (permission === "granted") {
					var notification = new Notification(text);
				}
			});
		}

		// At last, if the user has denied notifications, and you 
		// want to be respectful there is no need to bother them any more.
	}

	var chat_status_id = window.use_old_design ? "#chat_status" : "#status-chat-started";
	
  function advance_waiting_timer() {
		if(typeof window.now_we_are_talking == undefined) {
			window.now_we_are_talking = false;
		}
		if(!window.now_we_are_talking) {
			var status = $(chat_status_id).text();
			if(status.match(/^[0-9]+$/)) {
				if(status == RESTART_CHAT_TIMEOUT) {
					restartChat();
					return;
				}
				status = (parseInt(status) + 1).toString();
			} else {
				status = '0';
			}
			$(chat_status_id).text(status);
			setTimeout(advance_waiting_timer, 1000);
		}
	}
	
	function send_message(text) {
		$(chat_status_id).text('');
		$('#text').val(text);
		compat_sendNewMessage(text);
	}
		
	function first_message_is_hello(text) {
		for(var j = 0; j < window.RESPONSES.length; ++j) {
			var patterns = window.RESPONSES[j][1];
			var response = window.RESPONSES[j][0];
			for(var i = 0; i < patterns.length; ++i) {
				try {
					if(text.match(patterns[i])) {
						console.log(patterns[i]);
						if(response == undefined) {
							window.is_first_message = false;
							return restartChat;
						} else if(response == '') {
							return function() {};
						} else {
							$(chat_status_id).text('Auto...');
							return function() {
								setTimeout(function() { send_message(response); }, response.length * 100);
							};
						}
					}
				} catch(err) {
					alert("Error during matching expression '" + patterns[i] + "': " + err);
					console.log(patterns[i], err);
				}
			}
		}
		return undefined;
	}
	
	function get_only_my_responses(response_map) {
		var result = [];
		for(var i = 0; i < response_map.length; ++i) {
			if(response_map[i][0] != undefined) {
				result.push(response_map[i][0]);
			}
		}
		return result;
	}

	if(typeof(String.prototype.trim) === "undefined")
	{
		String.prototype.trim = function() 
		{
			return String(this).replace(/^\s+|\s+$/g, '');
		};
	}

	function find_response_group(target) {
		for(var j = 0; j < window.RESPONSES.length; ++j) {
			var patterns = window.RESPONSES[j][1];
			var response = window.RESPONSES[j][0];
			if(response == target) {
				return patterns;
			}
		}
		return null;
	}

	function subst_presets(expr, presets) {
		if(TEST) { console.log('SUBST: ' + expr); }
		for(var name in presets) {
			var placeholder = '{' + name + '}';
			var fuse = 100;
			while(fuse > 0 && expr.contains(placeholder)) {
				if(TEST) { console.log('FOUND PRESET: ' + placeholder); }
				expr = expr.replace(placeholder, '(' + presets[name] + ')');
				if(TEST) { console.log('REPLACED: ' + expr); }
				--fuse;
			}
		}
		if(TEST) { console.log('SUBST RESULT: ' + expr); }
		return expr;
	}
	function parse_responses(text) {
		var default_patterns = find_response_group(undefined);

		var presets = {};
		var data = text.split(/\n+/g);
		for(var i = 0; i < data.length; ++i) {
			var expr = data[i].trim();
			if(TEST) { console.log(expr); }
			try {
				if(expr.contains('=>')) {
					var parts = expr.split(/ *=> */g);
					if(parts.length != 2) {
						console.log("Cannot parse response: " + expr);
						continue;
					}
					var question = eval(subst_presets(parts[0], presets));
					var answer = eval(parts[1]);
					if(question == undefined || question.length == 0) {
						continue;
					}
					if(answer == undefined) {
						continue;
					}

					var answer_patterns = find_response_group(answer);
					if(answer_patterns != null) {
						answer_patterns.push(question);
					} else {
						window.RESPONSES.push([answer, [question]]);
					}
				} else if(expr.match(/^[A-Z_][A-Z_0-9]* *= */)) {
					expr = /^([A-Z][A-Z_0-9]*) *= *(.*)/.exec(expr);
					var name = expr[1];
					var preset = eval(expr[2]);
					if(preset == undefined || preset.length == 0) {
						continue;
					}
					preset = subst_presets(preset, presets);
					if(TEST) { console.log('PRESET: ' + name + ' = ' + preset); }
					presets[name] = preset;
				} else {
					expr = subst_presets(expr, presets);
					expr = eval(expr);
					if(expr == undefined) {
						continue;
					}
					if(expr.length == 0) {
						continue;
					}

					default_patterns.push(expr);
				}
			} catch(err) {
				alert("Error during parsing expression '" + expr + "': " + err);
				console.log(expr, err);
			}
		}

		return data.length;
	}
	if(TEST) {
		var TEST_RESPONSES = [
			'VAR= "[0-9]"',
			'/^[a-z]_{VAR}/i',
			'/^[a-z]_[0-9]/i',
			'/question/i => "answer"',
			'/question{VAR}/i => "answer"',
		].join('\n');
		if(window.RESPONSES == undefined) {
			window.RESPONSES = RESPONSES;
		}
		parse_responses(TEST_RESPONSES);
		TEST=false;
	}

	function load_responses(file_event) {
		if(typeof(file_event) === 'undefined') {
			file_event = undefined;
		}
		if(typeof window.CACHED == undefined) {
			window.CACHED = "";
		}

		window.RESPONSES = RESPONSES;

		if(file_event != undefined) {
			try {
				var pattern_count = parse_responses(file_event.target.result);
				console.log("Loaded " + pattern_count + " patterns.");
				window.CACHED = file_event.target.result;
				try {
					window.localStorage.setItem('responses', file_event.target.result);
					console.log("Saved cached patterns to local storage.");
				} catch(err) {
					alert("Error during saving local storage: " + err);
					console.log(err);
				}
			} catch(err) {
				alert("Error during loading responses text: " + err);
			}
		} else {
			var cached = null;
			try {
				cached = window.localStorage.getItem('responses');
				console.log("Reloaded cached patterns from local storage.");
			} catch(err) {
				alert("Error during loading local storage: " + err);
				console.log(err);
			}
			if(cached != null) {
				parse_responses(cached);
				window.CACHED = cached;
			} else if(window.CACHED != undefined) {
				parse_responses(window.CACHED);
				console.log("Reloaded cached patterns.");
			}
		}
	}
	$(window).focus(function() {
		window.FOCUSED = true;
	});

	$(window).blur(function() {
		window.FOCUSED = false;
	});

	var disconnected_id = window.use_old_design ? "div.disconnected" : 'div.ended';

	function watch_hanging_disconnect() {
		if(typeof window.end_chat_attempt == undefined) {
			window.end_chat_attempt = 0;
		}
		if(window.end_chat_attempt == undefined) {
			window.end_chat_attempt = 0;
		}
		if(typeof window.end_chat_notifications == undefined) {
			window.end_chat_notifications = 0;
		}
		if(window.end_chat_notifications == undefined) {
			window.end_chat_notifications = 0;
		}
		if($(disconnected_id).length) {
			window.end_chat_attempt += 1;
			if(window.end_chat_attempt > 25) {
				soundManager.play('disconnecting');
				notify("Disconnected.");
				window.end_chat_notifications += 1;
				//if(window.end_chat_notifications == 3) {
					setTimeout(compat_startNewChat, 350);
				//}
				window.end_chat_attempt = 0;
			}
		} else {
			window.end_chat_notifications = 0;
			window.end_chat_attempt = 0;
		}
		if(window.search_is_stuck == undefined) {
			window.search_is_stuck = 0;
		}
		if($('#searching')[0].style.display == "block") {
			window.search_is_stuck += 1;
			if(window.search_is_stuck > 200) {
				soundManager.play('disconnecting');
				notify("Search is stuck.");
				window.search_is_stuck = 0;
			}
		} else {
			window.search_is_stuck = 0;
		}
		setTimeout(watch_hanging_disconnect, 200);
	}

	function watch_modal_alert() {
		if($("div.modal-content").length && $("div.modal-content").is(':visible')) {
			evalAlertOk();
		}
		setTimeout(watch_modal_alert, 500);
	}

	// http://stackoverflow.com/a/1219983/2128769
	function htmlEncode(value){
		// Create a in-memory div, set its inner text (which jQuery automatically encodes)
		// Then grab the encoded contents back out. The div never exists on the page.
		return $('<div/>').text(value).html();
	}
	function htmlDecode(value){
		return $('<div/>').html(value).text();
	}

	function handle_long_message(text) {
		if(text.length > 131) {
			$('div#messages ol').append('<li>' + htmlEncode(text) + '</li>');
		}
	}


	var chat_header_id = window.use_old_design ? "div#header" : 'div#chat-header';
	$(chat_header_id).append('<label for="responses">Responses:</label><input id="responses" type="file">');
	$("#responses").click(function () {
		this.value = null;
	} );
	$("#responses").change( function() {
		var input = document.getElementById('responses');
		fr = new FileReader();
		fr.onload = load_responses; /*(e -> e.target.result)*/
		fr.readAsText(input.files[0]);
	} );
	watch_hanging_disconnect();
	load_responses();
	watch_modal_alert();

	window.onmessageIn = function(evt) {
		if(typeof window.is_first_message == undefined) {
			window.is_first_message = true;
		}
		if(typeof window.now_we_are_talking == undefined) {
			window.now_we_are_talking = false;
		}
		if(typeof window.FOCUSED == undefined) {
			window.FOCUSED = true;
		}
		if(typeof window.chat_is_stuck == undefined) {
			window.chat_is_stuck = 0;
		}
		if(window.chat_is_stuck == undefined) {
			window.chat_is_stuck = 0;
		}
		if(window.flood_counter == undefined) {
			window.flood_counter = 0;
		}
		if(window.last_message_time == undefined) {
			window.last_message_time = 0;
		}
		if(window.current_message_count == undefined) {
			window.current_message_count = 0;
		}
		if(window.my_messages == undefined) {
			window.my_messages = false;
		}
		chat_sound_on = false;

		var result = window.onmessageOut(evt);
    var msg_event = JSON.parse(evt.data);
		// {"action":"chat_connected","chat":"1463935535015c5299","opp_guid":"E8D7BF71-6DF1-4DA4-91CB-6455FADA3B42","version":null,"opp_unname":"Слон-1171"}
		// {"action":"user_connected","id":"ec25a1f76319974d2c598ddeb59777e9","guid":"28048DED-922F-4C12-975F-8B5B47DF02AE","logined":0,"unname":"Лисица-1819479","err_desc":null,"error_text":null}
		// {"action":"message_from_user","sender":"someone","message":"Чот все сонные такие","from":"e41775e2b1dcb4f636a2f765fa6dace5","chat":"1463935602711c3935"}
		// {"action":"user_writing","from":"e41775e2b1dcb4f636a2f765fa6dace5","chat":"1463935602711c3935"}
		// {"action":"chat_removed","reason":"user_leaved","chat":"1463935602711c3935"}
		if(msg_event.action == "hrt_response" && (window.is_first_message || !window.my_messages)) {
			window.chat_is_stuck += 1;
			if(window.chat_is_stuck >= 10 + 2 * window.current_message_count) {
				soundManager.play('disconnecting');
				notify("Chat is stuck.");
				//if(window.chat_is_stuck >= 12) {
					setTimeout(restartChat, 350);
				//}
			}
		} else if(msg_event.action == "user_writing") {
			window.chat_is_stuck = 0;
		}

    if(msg_event.action == "captcha_required") {
		window.my_messages = false;
		window.chat_is_stuck = 0;
		soundManager.play('disconnecting');
		notify("Captcha required.");
	}
    if(msg_event.action == "chat_connected") {
		if(!window.use_old_design) {
			$(chat_status_id).text('started');
		}
			window.my_messages = false;
			window.current_message_count = 0;
			window.chat_is_stuck = 0;
			window.is_first_message = true;
			window.now_we_are_talking = false;
			setTimeout(advance_waiting_timer, 1000);
		}
		if(msg_event.action == "chat_removed") {
			window.my_messages = false;
			window.chat_is_stuck = 0;
			window.now_we_are_talking = true;
		}
	  if(msg_event.action == "user_writing") {
			if(!window.now_we_are_talking) {
				window.now_we_are_talking = true;
			}
		}
		if(msg_event.action == "chat_removed") {
			if(window.is_first_message) {
				setTimeout(compat_startNewChat, 1000);
			} else {
				soundManager.play('disconnecting');
			}
		}
		if(msg_event.action == "message_from_user") {
			window.current_message_count++;
		}
		if(msg_event.action == "message_from_user" && msg_event.sender == 'someone') {
			var timestamp = Date.now();
			if(timestamp - window.last_message_time < 1000) {
				++window.flood_counter;
			} else {
				window.flood_counter = 0;
			}
			window.last_message_time = timestamp;
			if(window.flood_counter >= 5) {
				restartChat();
				window.flood_counter = 0;
			}

			if(!window.now_we_are_talking) {
				window.now_we_are_talking = true;
			}
 			if(window.is_first_message) {
				if(msg_event.message.match(/^Sticker:/)) {
					setTimeout(restartChat, 350);
				} else {
					var response = first_message_is_hello(msg_event.message.replace('\n', ' '));
					if(response) {
						setTimeout(response, 350);
					} else {
						soundManager.play('obtaining');
						notify(msg_event.message);
						window.is_first_message = false;
						handle_long_message(msg_event.message);
					}
				}
			} else {
				if(!window.FOCUSED) {
					notify(msg_event.message);
				}
				soundManager.play('obtaining');
				handle_long_message(msg_event.message);
			}
		}
		if(msg_event.action == "message_from_user" && msg_event.sender != 'someone') {
			window.my_messages = true;
		}
		var my_responses = get_only_my_responses(window.RESPONSES);
		if(!window.is_first_message && msg_event.action == "message_from_user" && msg_event.sender != 'someone' && my_responses.indexOf(msg_event.message) < 0) {
			soundManager.play('sending');
		}
		return result;
	}.bind(this);

	if(window.use_old_design) {
		var onmessageSource = window.WebSocketCreate.toString();
		onmessageSource = onmessageSource.replace("manSocket.onmessage =", 
				"manSocket.onmessage = function(evt) { return onmessageIn(evt); }; onmessageOut =");

		injectToFrame("WebSocketCreate = " + onmessageSource, window);

	} else {
		var onmessageSource = chat.createWebSocket.toString();
		onmessageSource = onmessageSource.replace("this.socket.onmessage =",
			"this.socket.onmessage = function(evt) { return onmessageIn(evt); }; onmessageOut =");

		injectToFrame("chat.createWebSocket = " + onmessageSource, window);
	}
	console.log('Userscript is successfully set.');

});
