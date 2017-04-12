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
  
  function restartChat() {
    closeCurrentChat();
    setTimeout(startNewChat, 1000);
  }

  $('#chat_close').click(function() {
		load_responses();
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
	
  function advance_waiting_timer() {
		if(typeof window.now_we_are_talking == undefined) {
			window.now_we_are_talking = false;
		}
		if(!window.now_we_are_talking) {
			var status = $('#chat_status').text();
			if(status.match(/^[0-9]+$/)) {
				if(status == RESTART_CHAT_TIMEOUT) {
					restartChat();
					return;
				}
				status = (parseInt(status) + 1).toString();
			} else {
				status = '0';
			}
			$('#chat_status').text(status);
			setTimeout(advance_waiting_timer, 1000);
		}
	}
	
	function send_message(text) {
		$('#chat_status').text('');
		$('#text').val(text);
		sendNewMessage();		
	}
		
	function first_message_is_hello(text) {
		for(var j = 0; j < window.RESPONSES.length; ++j) {
			var patterns = window.RESPONSES[j][1];
			var response = window.RESPONSES[j][0];
			for(var i = 0; i < patterns.length; ++i) {
				if(text.match(patterns[i])) {
					if(response == undefined) {
						window.is_first_message = false;
						return restartChat;
					} else if(response == '') {
						return function() {};
					} else {
					$('#chat_status').text('Auto...');
  					return function() {
						setTimeout(function() { send_message(response); }, response.length * 75);
					};
					}
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

	function parse_responses(text) {
		var default_patterns = find_response_group(undefined);

		var data = text.split(/\n+/g);
		for(var i = 0; i < data.length; ++i) {
			var expr = data[i].trim();
			if(expr.contains('=>')) {
				var parts = expr.split(/ *=> */g);
				if(parts.length != 2) {
					console.log("Cannot parse response: " + expr);
					continue;
				}
				var question = eval(parts[0]);
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
			} else {
				expr = eval(expr);
				if(expr == undefined) {
					continue;
				}
				if(expr.length == 0) {
					continue;
				}

				default_patterns.push(expr);
			}
		}

		return data.length;
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

	function watch_hanging_disconnect() {
		if(typeof window.end_chat_attempt == undefined) {
			window.end_chat_attempt = 0;
		}
		if(window.end_chat_attempt == undefined) {
			window.end_chat_attempt = 0;
		}
		if($('div.disconnected').length) {
			window.end_chat_attempt += 1;
			if(window.end_chat_attempt > 25) {
				soundManager.play('disconnecting');
				notify("Disconnected.");
				window.end_chat_attempt = 0;
			}
		} else {
			window.end_chat_attempt = 0;
		}
		setTimeout(watch_hanging_disconnect, 200);
	}

	$('div#header').append('<label for="responses">Responses:</label><input id="responses" type="file">');
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
		chat_sound_on = false;
		
		var result = window.onmessageOut(evt);
    var msg_event = JSON.parse(evt.data);
		// {"action":"chat_connected","chat":"1463935535015c5299","opp_guid":"E8D7BF71-6DF1-4DA4-91CB-6455FADA3B42","version":null,"opp_unname":"Слон-1171"}
		// {"action":"user_connected","id":"ec25a1f76319974d2c598ddeb59777e9","guid":"28048DED-922F-4C12-975F-8B5B47DF02AE","logined":0,"unname":"Лисица-1819479","err_desc":null,"error_text":null}
		// {"action":"message_from_user","sender":"someone","message":"Чот все сонные такие","from":"e41775e2b1dcb4f636a2f765fa6dace5","chat":"1463935602711c3935"}
		// {"action":"user_writing","from":"e41775e2b1dcb4f636a2f765fa6dace5","chat":"1463935602711c3935"}
		// {"action":"chat_removed","reason":"user_leaved","chat":"1463935602711c3935"}
    if(msg_event.action == "captcha_required") {
		soundManager.play('disconnecting');
		notify("Captcha required.");
	}
    if(msg_event.action == "chat_connected") {
			window.is_first_message = true;
			window.now_we_are_talking = false;
			setTimeout(advance_waiting_timer, 1000);
		}
		if(msg_event.action == "chat_removed") {
			window.now_we_are_talking = true;
		}
	  if(msg_event.action == "user_writing") {
			if(!window.now_we_are_talking) {
				window.now_we_are_talking = true;
			}
		}
		if(msg_event.action == "chat_removed") {
			if(window.is_first_message) {
				setTimeout(startNewChat, 1000);
			} else {
				soundManager.play('disconnecting');
			}
		}
		if(msg_event.action == "message_from_user" && msg_event.sender == 'someone') {
			if(!window.now_we_are_talking) {
				window.now_we_are_talking = true;
			}
 			if(window.is_first_message) {
				if(msg_event.message.match(/^Sticker:/)) {
					setTimeout(restartChat, 350);
				}
				var response = first_message_is_hello(msg_event.message.replace('\n', ' '));
				if(response) {
					setTimeout(response, 350);
				} else {
					soundManager.play('obtaining');
					notify(msg_event.message);
					window.is_first_message = false;
				}
			} else {
				if(!window.FOCUSED) {
					notify(msg_event.message);
				}
				soundManager.play('obtaining');
			}
    }
		var my_responses = get_only_my_responses(window.RESPONSES);
		if(msg_event.action == "message_from_user" && msg_event.sender != 'someone' && my_responses.indexOf(msg_event.message) < 0) {
			soundManager.play('sending');
		}
		return result;
	}.bind(this);

	var onmessageSource = window.WebSocketCreate.toString();
	onmessageSource = onmessageSource.replace("manSocket.onmessage =", 
		"manSocket.onmessage = function(evt) { return onmessageIn(evt); }; onmessageOut =");

	injectToFrame("WebSocketCreate = " + onmessageSource, window);
	console.log('Userscript is successfully set.');

});
