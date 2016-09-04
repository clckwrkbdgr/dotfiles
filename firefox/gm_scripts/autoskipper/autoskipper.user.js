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
var RESPONSES = [
		[ undefined, [
			/^.$/, /^(.)\1+$/, /^[0-9]+$/,

			/(гея )?(ищ[ую]|хочу) ([мжпд] |[мжпд][)]*$|би |парня|девушку|девочку|лезби|девчонку|женщину|даму|горячую|полненькую|послушн|взросл|зрелую|сочную|суч?ку|раба|гея|господина|лесби|подругу|строгую|прекрасн|похотлив|собеседницу|нижнюю|милого|милую|сладенькую|плохую|опытную|казашек)/i,

			/^(привет[,. !)]*)?(я|ты|вы|[0-9]+)? *([мждпM][,. )?0-9!]*$|[мждпMш][,. !)?0-9]+|[мпжд] *(или|,|\/|\\)? *[мпжд]([,. )?]|[,. )?]?$)|би[,. )]?$|парень|девушка|мальчик|девочка|гей|лесби|транс)/i,

			/пошл(ячк|еньк|ую|ого|ой|ая|ый|ых|ост)/i,
			/дроч(ил|им|у|ер|ить|ишь)/, /кончу /i, /помоги кончить/i, /отли(зал|жу)/i, /лизать/i, /кончил на/i, /возбуди/i, /шалить/i, /шалим/i, /дрочу/i, /мастурби/i,
			/пошалю/i,
			/[, ]вирт/i, /^вирт[ )]/i, /фотовирт/i, /секс/i, /скайп/i, /виpтик/i, /^вирт[?)]*$/i, /бдсм/i,
			/потраха/i, /трахал/i, / куни/i, /пид.р/i, /оттраха/i,
			/грудью/i, /прелести/i, /сис(и|ями|ьки|ечк|ек|ька)/i, /тит(ечки|ьки)/i, /письк/i, /скинь груд/i,
			/^покажи/i, /пока(жи|жите|зать)? *(себя|свою|свои|лицо|ножки|ноги|груд[ьи]|трус)/i, / фото([ .?)☺️!$]|чк|к)/i, /фотк/i, /фото$/i,
			/покажи свои/i, /порадуй ножками/i,
			/страпон/i, /интим/i, /минет/i, /фут *фетиш/i, /шлю[хш]/i, /извращен/i, /раб(ын|ом)/i, /госпож/i, /разврат/i, / член/i, /^член$/i, /пенис/i, /страстн/i,
			/трусики/i, /нудист/i, /курвочку/i,
			/^[0-9]+ *см/i,
			/^девушк.*есть[?]*$/i,
			/^сук[аи]/, /сучк[ауи]/i, /иди(те)? на *хуй/i,
			/^удиви( |$)/i, /^яой/i, /чилдрен порн/i,

			/^пр(иф|еф|ев)?$/i,		
			/как (зовут|звать) тебя[?)]*$/i, /как (тебя|вас) (зовут|звать)[,?) :]*$/i, /как (зовут|звать)[? )]*$/i, /^имя.?$/i,
			/^ты кто/i, /^кто[?]?$/i,	/^кто ты[?]/i,	
			/^ч[ёе] как/i,
			/^(мне )?[0-9]+ лет/i,
			/^(ск|сколько|скок) (тебе *)?лет[ ?]*/i,
			/^(ты )?откуда/i,
			/^(привет[., ])?(я )?(макс|егор|влад|боря|иван|дима|Олег|саня|сергей|павел|евгений|дмитрий|ваня|вова|стас|игорь|дима|витя|илья|алексей|артем|валентин|георгий|арсений|миша|андрей|рома|вася|коля|николай|александр|кирилл|гоша|дани+л|никита|костя|сергей|паша|михаил)/i,
			/^(привет[., ])?(я )?(лиза|алина|наст[яь]|маша|наташа|Кристина|юля|вика)/i,
			/^(спб|екб|мск|питер|москва|новосиб|киев|магнитогорск|казахстан|воркута)/i,

			/https?:/i,
			/^мур( мур)?[:3 ]*$/i, /^мяу$/i, /^гоу? /i, /^(лол|кек)/i, /кис кис кис/i, /^зиг/i,
			/Приветствуем! Вы попали в наш много.ользовательский .*чат/i, /Приветствуем! Вы попали в многоnользовательский чат./i,
			/пьян/i,
			/^\/postcount/i,

			/ точк[аи][)?]*$/i, /^то+чк[аи]/i, /с точкой$/i, /точечка/i, /(все *(настолько)?|как) *серь.зно[)]?$/i, /^загадочно так/, /грозно[?]*/i,
			/ставить точк./i, /^с точкой/i, /много точек/i, /точка в конце/i, /с точкой/i,

			/^пи+у([ -?]|$)/i, /сосновое деревце/i, /ты украл мой кот[её]л/i, /капрал.?/i, /Зачем выдре терьер/i, /^сг[?]*$/i, /slava EVROPEYSKOMU SOYUZU/i,
			/цп в лс/i, /Может.? тебе по[д]?стричься/i, /Где Грейнджер[?]/i, /^42/i, /^внутри пустота/i, /^вож[?]*$/i, /^ехет/i, /та и на небе тучи/i,
			/се[нм]па+[йя]/i, /^эрен[?]/i, /^ларри (и[сз] р[еи]ал|реальнее)/i, / ис риал$/i, /хетагугл/i, /^сосна/i, /дорито/i, /са+йфер/i, /пропал крыжовник/i, /Клоун-дальнобойщик/i,
			/ветер и дождь/i, /мб[еэ]нд/i, /MBAND/i, /ТАБОР/, /фикрайтеры выходите/i, /каким шампунем ты пользуешься/i, /патим[еэ]йкер/i, /татака[еэ]/i, /картошка на базаре/i,
			/хиз[еэ]+нс/i, /твит+[ео]р/i, /^тви[?)]*$/i, /Привет, Антош/i, /антош, привет/i, /феечка.*пыльцы/i, /mur mur/i, /еее рок/i, /^дирик/i, /^б ищет д/i, /За кем стоит андеграунд/i,
			/^гк[,.)!?]*$/i, /^гк /i, /курлык/i, /биллдип/i, /сосенка/i, /чудо вокруг/i, /иван *гай/i, /бабулька/i, /лучший футболист/i, /ирландские попки/i, /^нб[?]*$/i,
			/(ГДЕ СПРЯТАТЬ ТЕЛО|ГДЕ ТЕЛО СПРЯТАТЬ)/i, /С.сси ?Луис/i, /когтевран/i, /пернатая[ ]*братва/i, /кридоман/i, /^ек[?]*$/i, /(ищу|в поисках) с.сси/i,
			/Харли Квин/i, /ТОЛЬКО ВМЕСТЕ МЫ СИЛЬНЫ/i, /дратути/i, /^дч[?]*$/i, /^девчат$/i, /нико.нико.ни/i, /pidrilina/i, /кто проживает на дне океана/i,
			/что такое .?слэш.?/i, /Листья танцуют под силой юности глаз мстителя/i, /^фк[?]?$/i, /киллджой/i, /Хочу азиаток с фото/i,
			/ты не шаришь/i
		]	],
		[ 'Нет, это у тебя вопросы шаблонные.', [
			/^Ты бот.?$/i
		]	],
		[ 'Здравствуй.', [
			/^Приветствую.?$/i
		]	],
		[ 'Привет.', [
			/^[.]*(пр+и+в+[еэі]+[тиь].?|прив)[ ^_?;:.30)!сc]*(собеседник)?$/i, /^привте$/i, /^приветики?[ :з)]?$/i, /^привки$/i,
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
			/^(ну )?как (дела+|жизнь|жиза|настрой|настроени[ея])[?) \\]*$/i
		]	],
		[ 'Спокойно. А у тебя?', [
			/^как (прош.л)? *(твой)? *(день|вечер) *(складывается|проходит|прош.л)?[?) ]*$/i
		]	],
		[ 'Хорошо. И у вас.', [
			/^как ваше настроение[?) ]*$/i, /^как ваши дела[? )]*$/i, /^как ваша жизнь[? )]*$/i
		]	],
		[ 'Хорошо. И вы.', [
			/^как вы[?) ]*$/i
		]	],
		[ 'Хорошо. И ты.', [
			/^как (ты|поживаешь)( там)?[?) ]*$/i
		]	],
		[ 'Собеседников ищу, как и ты.', [
			/^чем занимаешься[?) ]*$/i, /^ч(то|е) делаешь[?) ]*$/i
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
				var response = first_message_is_hello(msg_event.message.replace('\n', ' '));
				if(response) {
					setTimeout(response, 350);
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
