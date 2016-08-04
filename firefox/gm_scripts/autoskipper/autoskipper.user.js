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
    setTimeout(startNewChat, 500);
  }
  
  $('#chat_close').click(function() {
		load_responses();
    restartChat();
  });

	var RESTART_CHAT_TIMEOUT = '5'; // seconds.
	var RESPONSE_JS_URL = "https://localhost/response.js";
var RESPONSES = [
		[ undefined, [
			/^.$/, /^(.)\1+$/, /^[0-9]+$/,

			/(гея )?(ищ[ую]|хочу) ([мжпд] |[мжпд]$|би |парня|девушку|девочку|девчонку|женщину|даму|горячую|полненькую|послушн|взросл|зрелую|суч?ку|раба|гея|господина|лесби|подругу|строгую|прекрасн|похотлив|собеседницу|нижнюю|милого)/i,

			/^(привет[,. !)]*)?(я|ты|вы|[0-9]+)? *([мждпM][,. )?0-9!]*$|[мждпMш][,. !)?0-9]+|[мпжд] *(или|,|\/|\\)? *[мпжд]([,. )?]|[,. )?]?$)|би[,. )]?$|парень|девушка|мальчик|девочка|гей|лесби)/i,

			/пошл(ячк|еньк|ую|ого|ой|ая|ый|ых|ост)/i,
			/дроч(у|ер|ить|ишь)/, /кончу /i, /помоги кончить/i, /отли(зал|жу)/i, /лизать/i, /кончил на/i, /возбуди/i, /шалить/i, /шалим/i, /дрочу/i, /мастурби/i,
			/[, ]вирт/i, /^вирт[ )]/i, /фотовирт/i, /секс/i, /скайп/i, /виpтик/i, /^вирт[?)]*$/i, /бдсм/i,
			/потрахаем/i, /трахал/i, / куни/i,
			/грудью/i, /прелести/i, /сис(и|ями|ьки|ечки|ек|ька)/i, /тит(ечки|ьки)/i, /письк/i, /покажи грудь/i,
			/пока(жи|жите|зать)? *(себя|свою|свои|лицо|груд[ьи]|трус)/i, / фото[ .?)☺️!$]/i, /фотк/i, /фото$/i,
			/покажи свои/i,
			/страпон/i, /интим/i, /минет/i, /фут *фетиш/i, /шлю[хш]/i, /извращен/i, /раб(ын|ом)/i, /госпож/i, /разврат/i, / член/i, /^член$/i, /пенис/i, /страстн/i,
			/трусики/i,
			/^[0-9]+ *см/i,
			/^девушк.*есть[?]*$/i,
			/^сук[аи]/,

			/^пр(иф|еф|ев)?$/i,		
			/как (зовут|звать) тебя[?)]*$/i, /как (тебя|вас) (зовут|звать)[,?) :]*$/i, /как (зовут|звать)[? )]*$/i, /^имя.?$/i,
			/^ты кто/i, /^кто[?]?$/i,	/^кто ты[?]/i,	
			/^ч[ёе] как/i,
			/^(ск|сколько|скок) лет[ ?]*/i,
			/^(ты )?откуда/i,
			/^(привет[., ])?(я )?(макс|влад|боря|дмитрий|дима|витя|алина|наст[яь]|алексей|олег|валентин|георгий|миша|андрей|маша|наташа|рома|вася|коля|александр|кирилл|гоша|дани+л|никита|костя|сергей)/i,
			/^(спб|екб|мск|питер|москва|новосиб|киев|магнитогорск|казахстан)/i,

			/https?:/i,
			/^мур( мур)?[:3 ]*$/i, /^мяу$/i, /^гоу? /i, /^(лол|кек)/i,
			/Приветствуем! Вы попали в наш многопользовательский "чат в чате"/i,
			/пьян/i,
			/^\/postcount/i,

			/ точка[)?]*$/i, /^то+чк[аи]/i, /с точкой$/i, /точечка/i, /все *(настолько)? *серьезно[)]?$/i, /^загадочно так/, /грозно[?]*/i,

			/^пи+у([ -?]|$)/i, /сосновое деревце/i, /ты украл мой кот[её]л/i, /капрал.?/i, /Зачем выдре терьер/i, /^сг[?]*$/i, /slava EVROPEYSKOMU SOYUZU/i,
			/цп в лс/i, /Может.? тебе по[д]?стричься/i, /Где Грейнджер[?]/i, /^42/i, /^внутри пустота/i, /^вож[?]*$/i, /^ехет/i, /та и на небе тучи/i,
			/се[нм]па+[йя]/i, /^эрен[?]/i, /^ларри (и[сз] р[еи]ал|реальнее)/i, / ис риал$/i, /хетагугл/i, /^сосна/i, /дорито/i, /са+йфер/i, /пропал крыжовник/i, /Клоун-дальнобойщик/i,
			/ветер и дождь/i, /мб[еэ]нд/i, /MBAND/i, /ТАБОР/, /фикрайтеры выходите/i, /каким шампунем ты пользуешься/i, /патим[еэ]йкер/i, /татака[еэ]/i, /картошка на базаре/i,
			/хиз[еэ]+нс/i, /твит+[ео]р/i, /^тви[?)]*$/i, /Привет, Антош/i, /антош, привет/i, /феечка.*пыльцы/i, /mur mur/i, /еее рок/i, /^дирик/i, /^б ищет д/i, /За кем стоит андеграунд/i,
			/^гк[,.)!?]*$/i, /^гк /i, /курлык/i, /биллдип/i, /сосенка/i, /чудо вокруг/i, /иван *гай/i, /бабулька/i, /лучший футболист/i, /ирландские попки/i, /^нб[?]*$/i,
			/(ГДЕ СПРЯТАТЬ ТЕЛО|ГДЕ ТЕЛО СПРЯТАТЬ)/i, /С.сси ?Луис/i,
			/ты не шаришь/i
		]	],
		[ undefined, [
			/^гк[,.)!?]*$/i, /^гк /i, /курлык/i, /биллдип/i, /сосенка/i, /чудо вокруг/i, /иван *гай/i, /бабулька/i, /лучший футболист/i
		]	],
		[ 'Здравствуй.', [
			/^Приветствую.?$/i
		]	],
		[ 'Привет.', [
			/^[.]*(пр+и+в+[еэі]+[тиь]|прив)[ ^?;:.30)!]*(собеседник)?$/i, /^привте$/i, /^приветики?[ :з)]?$/i, /^привки$/i,
			/^х[аеэ]+й.?$/i,
			/^алоха.?$/i, /^бонжур/i, /^х[эеа]л+оу?$/i,
			/^Ку+$/i, /^ку-?ку/i,
			/^йо+у?$/i,
			/^салют/i,
			/^ал+о$/i,
			/^(добрый вечер|вечер добрый)[. ?)!]*$/i, /^доброго вечера/i, /^добро(е|го) врем(я|ени) суток[. ?]*$/i,
			/^з?дра+сь*т[еи][ ).?^]*/i, /^здравствуйте.?$/i, /^здрав?ствуй[?)cс:.]*$/i, /^[з]?д[ао]ров(а)?$/i, /^здаровки/i
		]	],
		[ 'Шевелится.', [
			/^как оно[?) ]*$/i
		]	],
		[ 'Хорошо. И у тебя.', [
			/^как (дела|жизнь|настроени[ея])[?) ]*$/i
		]	],
		[ 'Спокойно. А у тебя?', [
			/^как (прошёл)? *(твой)? *(день|вечер) *(складывается|прош.л)?[?) ]*$/i
		]	],
		[ 'Хорошо. И ваше.', [
			/^как ваше настроение[?) ]*$/i
		]	],
		[ 'Хорошо. И вы.', [
			/^как вы[?) ]*$/i
		]	],
		[ 'Хорошо. И ты.', [
			/^как ты[?) ]*$/i
		]	],
		[ 'Собеседников ищу, как и ты.', [
			/^чем занимаешься[?) ]*$/i
		] ]
	]

	
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
  					return function() { send_message(response); };
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

	function load_responses() {
		window.RESPONSES = RESPONSES;
		/*
		$.get(RESPONSE_JS_URL, function(data) {
			window.RESPONSES = eval(data);
		}).done(function() { console.log("Done loading responses. OK"); }).fail(function() { alert("Failed to load responses."); });
		*/
	}
	
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
    if(msg_event.action == "user_connected") {
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
				setTimeout(startNewChat, 500);
			} else {
				soundManager.play('disconnecting');
			}
		}
		if(msg_event.action == "message_from_user" && msg_event.sender == 'someone') {
			if(!window.now_we_are_talking) {
				window.now_we_are_talking = true;
			}
 			if(window.is_first_message) {
				var response = first_message_is_hello(msg_event.message);
				if(response) {
					setTimeout(response, 500);
				} else {
					soundManager.play('obtaining');
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
