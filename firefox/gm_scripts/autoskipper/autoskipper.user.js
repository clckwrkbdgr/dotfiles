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
 * Empty lines are ignored.
 * Local storage should be available (set cookies for https://chatvdvoem.ru).
 */

	var RESTART_CHAT_TIMEOUT = '5'; // seconds.
var RESPONSES = [
		[ undefined, [
			/^.$/, /^(.)\\1+$/, /^[0-9]+$/
		]	],
		[ 'Нет, это у тебя вопросы шаблонные.', [
			/^Ты (че)? *бот *(что ли)?.?$/i, /^это.*бот[?]?/i
		]	],
		[ 'Здравствуй.', [
			/^Приветствую.?$/i
		]	],
		[ 'Привет.', [
			/^(ну[,]? )?[.]*(пр+и+[ву]+[еэі]+[тиь].?|прива?|пиривет)[ ^_?;:.30)!сc]*(собеседник)?.?$/i,
			/^привте$/i, /^ривет$/i, /^пивет$/, /^тевирп$/i,
			/^приветики?[! .:з)]?$/i, /^привки$/i,
			/^привет что ли/i,
			/^э?х[аеэ]+й[.)~]?$/i,
			/^алоха.?$/i, /^бонжур/i, /^х[эеа]л+о+у?[.]?$/i,
			/^Ку+$/i, /^ку-?ку/i,
			/^салам$/i,
			/^йо+у?$/i,
			/^салют/i,
			/^ал+о$/i,
			/^hello$/i,
			/^(добрый веч.р|вечер добрый)[. ?)!:^]*$/i, /^доброго вечера/i, /^добро(е|го) врем(я|ени) суток[. ?]*$/i, /^добрый день$/i,
			/^з?дра+сь*т[ьеи][ ).?^]*$/i, /^здравствуйте.?$/i, /^(ну )?здрав?ствуй[?)cс:.]*$/i, /^[з]?д[ао]ров(а)?[.]?$/i, /^здаровки/i
		]	],
		[ 'Шевелится.', [
			/^как оно[?) ]*$/i
		]	],
		[ 'Хорошо. А у тебя?', [
			/^(ну )?как (тво. )?(дела+|делишки|жизнь|жиза|настрой|настроени([ея]|це))( молодая)?[?) \\:D]*$/i
		]	],
		[ 'Спокойно. А у тебя?', [
			/^как (прош.л)? *(твой)? *(денек|день|вечер|выходные) *(складывается|проходит|прош.л)?[?) ]*$/i
		]	],
		[ 'Хорошо. А у вас?', [
			/^как ваше настроение[?) ]*$/i, /^как ваши дела[? )]*$/i, /^как ваша жизнь[? )]*$/i
		]	],
		[ 'Хорошо. А вы?', [
			/^как вы[?) ]*$/i
		]	],
		[ 'Хорошо. А ты?', [
			/^как (ты|поживаешь)( там)?[?) ]*$/i
		]	],
		[ 'Собеседников ищу, а ты?', [
			/^чем занимаешься[?) ]*$/i, /^(ч(то|е|его)|шо+) (ты|тут|здесь)? *делаешь[!?) ]*$/i
		] ]
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

	function parse_responses(text) {
		var default_patterns = null;
		for(var j = 0; j < window.RESPONSES.length; ++j) {
			var patterns = window.RESPONSES[j][1];
			var response = window.RESPONSES[j][0];
			if(response == undefined) {
				default_patterns = patterns;
				break;
			}
		}

		var data = text.split(/\n+/g);
		for(var i = 0; i < data.length; ++i) {
			var expr = data[i].trim();
			expr = eval(expr);
			if(expr == undefined) {
				continue;
			}
			if(expr.length == 0) {
				continue;
			}

			default_patterns.push(expr);
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

	function watch_hanging_disconnect() {
		if(typeof window.end_chat_attempt == undefined) {
			window.end_chat_attempt = 0;
		}
		if(window.end_chat_attempt == undefined) {
			window.end_chat_attempt = 0;
		}
		if($('div.disconnected').length) {
			window.end_chat_attempt += 1;
			console.log(window.end_chat_attempt);
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
					notify("First message!\n" + msg_event.message);
					window.is_first_message = false;
				}
			} else {
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
